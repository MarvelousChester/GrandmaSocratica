"""The simulation as a service: base menus + day profiles -> simulated days.

Days run as one continuous season from day 0 (opening day), so The Bakery's
repricing in response to grandma's profiles is part of every day served.
Kept free of HTTP so it can be driven from scripts and tests as easily as from
the API.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel

from ..core.enums import Bakery
from ..menu import store as menu_store
from ..menu.costing import Pantry, RecipeBook
from ..menu.items import Menu
from ..menu.recipes_seed import recipe_books_by_bakery
from ..menu.seed import build_menus
from ..profiles.ingredients import IngredientPrices
from ..profiles.overrides import DayProfile
from ..profiles.store import ScheduledIngredientPrices, ScheduledProfile, ScheduleStore
from ..simulation.day import DayConfig, DayResult, DaySimulator, menu_prices, random_seed
from ..simulation.season import DayRecord, SeasonConfig, SeasonResult, SeasonSimulator

# Simulated days kept in memory before the cache is dropped and rebuilt.
_MAX_CACHED_DAYS = 2000


class _CachedDay(NamedTuple):
    record: DayRecord
    result: DayResult


class SimulationService:
    """Simulates numbered days (0, 1, 2, ...) for one fixed town of customers.

    Day N is the last day of a season run from day 0 under the stored
    profiles, so it reflects every price move made before it -- grandma's and
    The Bakery's answers to them. Each day's seed is its number, customers
    expect the base menu prices, and `season_config` fixes everything else
    (population, clock, choice model, competitor policy).

    Simulated days are cached by the base menus and the profiles that can
    affect them, so walking forward one day at a time doesn't re-run history,
    and changing a profile only invalidates the days from it onward.
    """

    def __init__(
        self,
        db_path: str | Path = menu_store.DEFAULT_DB_PATH,
        season_config: SeasonConfig | None = None,
        recipe_books: dict[Bakery, RecipeBook] | None = None,
    ):
        self.db_path = Path(db_path)
        self.season_config = season_config or SeasonConfig()
        self.recipe_books = recipe_books or recipe_books_by_bakery()
        self.profiles = ScheduleStore(self.db_path, "day_profiles", "profile", DayProfile)
        self.ingredient_prices = ScheduleStore(
            self.db_path, "day_ingredient_prices", "prices", IngredientPrices
        )
        self._cache: dict[str, _CachedDay] = {}
        self._seed_menus_if_empty()

    def _seed_menus_if_empty(self) -> None:
        with closing(menu_store.connect(self.db_path)) as conn:
            menu_store.init_schema(conn)
            if not menu_store.menu_rows(conn):
                for menu in build_menus():
                    menu_store.save_menu(conn, menu)

    def base_menus(self) -> list[Menu]:
        """Menus as stored, read fresh so edits to the menu DB show up live."""
        with closing(menu_store.connect(self.db_path)) as conn:
            return [menu_store.load_menu(conn, bakery) for bakery in Bakery]

    def profile_for(self, day: int) -> ScheduledProfile:
        latest = self.profiles.latest(day)
        if latest is None:
            return ScheduledProfile(day=day, source_day=None, profile=DayProfile())
        return ScheduledProfile(day=day, source_day=latest[0], profile=latest[1])

    def list_profiles(self) -> list[ScheduledProfile]:
        return [
            ScheduledProfile(day=day, source_day=day, profile=profile)
            for day, profile in self.profiles.all().items()
        ]

    def set_profile(self, day: int, profile: DayProfile) -> ScheduledProfile:
        """
        Set the profile for `day` onward, until a later day sets its own.

        Args:
         day: First day the profile applies to.
         profile: Item overrides for those days.

        Returns:
         The profile now in force on `day`.

        Raises:
         ValueError: If the profile names unknown items or yields invalid ones.
        """
        profile.apply(self.base_menus())
        self.profiles.set(day, profile)
        return self.profile_for(day)

    def clear_profile(self, day: int) -> bool:
        """Drop the profile set on `day`; the previous one carries over again."""
        return self.profiles.delete(day)

    def base_pantries(self) -> dict[Bakery, Pantry]:
        return {bakery: book.pantry for bakery, book in self.recipe_books.items()}

    def pantries_for(self, day: int) -> dict[Bakery, Pantry]:
        """Each bakery's ingredient prices as they stand on `day`."""
        prices = self.ingredient_prices_for(day).prices
        return {
            bakery: book.pantry for bakery, book in prices.apply(self.recipe_books).items()
        }

    def ingredient_prices_for(self, day: int) -> ScheduledIngredientPrices:
        latest = self.ingredient_prices.latest(day)
        if latest is None:
            return ScheduledIngredientPrices(
                day=day, source_day=None, prices=IngredientPrices()
            )
        return ScheduledIngredientPrices(day=day, source_day=latest[0], prices=latest[1])

    def list_ingredient_prices(self) -> list[ScheduledIngredientPrices]:
        return [
            ScheduledIngredientPrices(day=day, source_day=day, prices=prices)
            for day, prices in self.ingredient_prices.all().items()
        ]

    def set_ingredient_prices(
        self, day: int, prices: IngredientPrices
    ) -> ScheduledIngredientPrices:
        """
        Set ingredient prices from `day` onward, until a later day sets its own.

        Args:
         day: First day the prices apply to.
         prices: Multipliers and per-bakery prices over the base pantries.

        Returns:
         The prices now in force on `day`.

        Raises:
         ValueError: If an ingredient or bakery is unknown.
        """
        prices.apply(self.recipe_books)
        self.ingredient_prices.set(day, prices)
        return self.ingredient_prices_for(day)

    def clear_ingredient_prices(self, day: int) -> bool:
        """Drop the prices set on `day`; the previous ones carry over again."""
        return self.ingredient_prices.delete(day)

    def menus_for(self, day: int) -> list[Menu]:
        """Both menus as they stood on `day`, competitor repricing included."""
        return self.simulate(day).menus

    def simulate(self, day: int) -> DayResult:
        return self._day(day).result

    def simulate_menus(self, menus: list[Menu], seed: int | None = None) -> DayResult:
        """
        Simulate one standalone day for menus given as-is, outside the season.

        Same town, clock and choice model as the season, and customers expect
        the base menu prices, so a dearer item is still judged as a markup;
        items not on the base menus are taken at face value. There is no
        history: no competitor repricing, no habits. Seed 0 with the base
        menus gives exactly day 0.

        Args:
         menus: Up to one menu per bakery.
         seed: Varies arrivals and choices. None draws a random one, so
          repeated runs differ; the seed used is in the result's config.

        Returns:
         The simulated day, ledger included.

        Raises:
         ValueError: If a bakery has two menus, an item sits on another
          bakery's menu, or two items share an id.
        """
        self.check_menus(menus)
        config = self.season_config
        return DaySimulator(
            DayConfig(
                seed=random_seed() if seed is None else seed,
                population_seed=config.population_seed,
                population=config.population,
                clock=config.clock,
                choice=config.choice,
                usual_prices=menu_prices(self.base_menus()),
            ),
            menus,
            self.recipe_books,
        ).run()

    @staticmethod
    def check_menus(menus: list[Menu]) -> None:
        """Raise ValueError unless menus are one per bakery with unique item ids."""
        bakeries: set[Bakery] = set()
        item_ids: set[str] = set()
        for menu in menus:
            if menu.bakery in bakeries:
                raise ValueError(f"two menus for bakery {menu.bakery.value!r}")
            bakeries.add(menu.bakery)
            for item in menu.items:
                if item.bakery is not menu.bakery:
                    raise ValueError(
                        f"item {item.id!r} belongs to {item.bakery.value!r} "
                        f"but is on {menu.bakery.value!r}'s menu"
                    )
                if item.id in item_ids:
                    raise ValueError(f"item id {item.id!r} is used twice")
                item_ids.add(item.id)

    def season(self, through: int) -> SeasonResult:
        """Days 0..`through` as a timeline: prices, sales, ledger, repricings."""
        records = [self._day(day).record for day in range(through + 1)]
        simulator = SeasonSimulator(self._season_config(through), self.base_menus())
        return SeasonResult(
            config=simulator.config, rivalries=simulator.rivalries, days=records
        )

    def _season_config(self, through: int) -> SeasonConfig:
        return self.season_config.model_copy(
            update={
                "days": through + 1,
                "profiles": self.profiles.all(),
                "ingredient_prices": self.ingredient_prices.all(),
            }
        )

    def _day(self, day: int) -> _CachedDay:
        """
        Fetch day `day` from the cache, running the season up to it if needed.

        A miss re-runs the season from day 0 and caches every day it passes,
        so earlier days are hits afterwards.

        Args:
         day: Day number, from 0.

        Returns:
         The day's season record and full result.
        """
        base_menus = self.base_menus()
        config = self._season_config(day)
        key = self._cache_key(day, base_menus, config)
        if key not in self._cache:
            if len(self._cache) > _MAX_CACHED_DAYS:
                self._cache.clear()
            simulator = SeasonSimulator(config, base_menus, self.recipe_books)
            for record, result in simulator.iter_days():
                self._cache[self._cache_key(record.day, base_menus, config)] = _CachedDay(
                    record, result
                )
        return self._cache[key]

    @staticmethod
    def _cache_key(day: int, base_menus: list[Menu], config: SeasonConfig) -> str:
        """Identifies everything day `day` depends on: the base menus and the
        profiles and ingredient prices set on or before it."""

        def up_to_day(schedule: dict[int, BaseModel]) -> dict[int, dict]:
            return {d: v.model_dump(mode="json") for d, v in schedule.items() if d <= day}

        payload = {
            "day": day,
            "menus": [m.model_dump(mode="json") for m in base_menus],
            "profiles": up_to_day(config.profiles),
            "ingredient_prices": up_to_day(config.ingredient_prices),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
