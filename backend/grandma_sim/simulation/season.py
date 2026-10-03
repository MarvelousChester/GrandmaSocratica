"""Run a stretch of days, with The Bakery repricing as it goes.

A single day can't show a reaction -- grandma changes a price on day 2 and the
answer comes on day 7. This strings days together and lets the competitor
reprice between them.

Grandma's own moves are `DayProfile`s, the same overrides the API serves, and
carry forward until a later day replaces them. The Bakery's responses are held
separately and layered on top, so the player's profile never wipes a price the
competitor set.

Customers are fixed for the whole run (one `population_seed`) while each day
re-rolls arrivals and decisions, so a change in share is attributable to the
prices rather than to a different crowd turning up.

Customers remember, though. What they expect to pay drifts toward what they
were charged, so a rise hurts most at first and is slowly accepted (and a long
discount makes the old price feel like a markup). And each purchase builds a
habit for that bakery, so customers won or lost stay that way for a while.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from typing import TypeVar

from pydantic import BaseModel, Field

from ..choice.model import ChoiceConfig
from ..competition.pricing import CompetitorPricer, PricingPolicy, Repricing
from ..competition.rivalry import Rivalry, find_rivalries
from ..core.clock import DayClock
from ..core.enums import Bakery
from ..customers.population import PopulationConfig
from ..customers.presets import default_population
from ..menu.costing import RecipeBook
from ..menu.items import Menu
from ..profiles.ingredients import IngredientPrices
from ..profiles.overrides import DayProfile
from .day import DayConfig, DayResult, DaySimulator, menu_prices
from .events import DaySummary
from .habits import HabitConfig, Habits, mean_habit
from .ledger import DayLedger

# Keeps per-day seeds far apart so consecutive days don't correlate.
_DAY_SEED_STRIDE = 100_000

T = TypeVar("T")


def _pairs(rivalries: Sequence[Rivalry]) -> set[tuple[str, str]]:
    """Just who tracks whom, for spotting that the map changed."""
    return {(r.watcher_id, r.rival_id) for r in rivalries}


def in_force(schedule: Mapping[int, T], day: int) -> T | None:
    """The value set most recently on or before `day`, or None if none yet."""
    applicable = [d for d in schedule if d <= day]
    return schedule[max(applicable)] if applicable else None


class SeasonConfig(BaseModel):
    """Everything that defines a run of days."""

    days: int = Field(28, ge=1)
    seed: int = Field(0, description="Varies arrivals and choices day to day.")
    population_seed: int = Field(0, description="Fixes who lives in town.")
    population: PopulationConfig = Field(default_factory=default_population)
    clock: DayClock = Field(default_factory=DayClock)
    choice: ChoiceConfig = Field(default_factory=ChoiceConfig)
    policy: PricingPolicy = Field(default_factory=PricingPolicy)

    reactive: bool = Field(
        True, description="False freezes The Bakery's prices, for a baseline run."
    )
    profiles: dict[int, DayProfile] = Field(
        default_factory=dict,
        description="Grandma's moves: the profile set on a day holds until replaced.",
    )
    ingredient_prices: dict[int, IngredientPrices] = Field(
        default_factory=dict,
        description="Ingredient price changes; each holds until replaced. Costs only.",
    )
    price_memory: float = Field(
        0.05,
        ge=0.0,
        le=1.0,
        description=(
            "Share of the gap between usual and charged price closed each day; "
            "0 keeps customers expecting the base menu prices forever."
        ),
    )
    habits: HabitConfig = Field(default_factory=HabitConfig)


class DayRecord(BaseModel):
    """One day of the season: what was charged, what sold, what moved."""

    day: int
    prices: dict[str, float] = Field(description="Every item's price that day.")
    usual_prices: dict[str, float] = Field(
        description="What customers expected each item to cost going into the day."
    )
    habit: dict[Bakery, float] = Field(
        description="Average habit per bakery across the town going into the day."
    )
    summary: DaySummary
    ledger: DayLedger | None = Field(
        None, description="Costs and profit; None when no recipe books were given."
    )
    rivalries: list[Rivalry] | None = Field(
        None,
        description="The refreshed map, on review days where it changed. Else None.",
    )
    repricings: list[Repricing] = Field(default_factory=list)


class SeasonResult(BaseModel):
    config: SeasonConfig
    rivalries: list[Rivalry]
    days: list[DayRecord]

    def share_series(self, bakery: Bakery) -> list[float]:
        return [record.summary.market_share(bakery) for record in self.days]

    def revenue_series(self, bakery: Bakery) -> list[float]:
        return [record.summary.by_bakery[bakery].revenue for record in self.days]

    def profit_series(self, bakery: Bakery) -> list[float]:
        """Gross profit per day (revenue - ingredient cost). Needs recipe books."""
        if any(record.ledger is None for record in self.days):
            raise ValueError("season was run without recipe books, so has no costs")
        return [
            record.ledger.bakeries[bakery].financials.profit for record in self.days
        ]

    def all_repricings(self) -> list[Repricing]:
        return [r for record in self.days for r in record.repricings]


class SeasonSimulator:
    """Days in sequence, with one menu reacting to the other between them."""

    def __init__(
        self,
        config: SeasonConfig,
        base_menus: list[Menu],
        recipe_books: Mapping[Bakery, RecipeBook] | None = None,
    ):
        self.config = config
        self.base_menus = [menu.model_copy(deep=True) for menu in base_menus]
        self.recipe_books = recipe_books
        self.usual_prices = menu_prices(self.base_menus)

        by_bakery = {menu.bakery: menu for menu in self.base_menus}
        self.rivalries = self.rivalries_for(self.base_menus)
        self.pricer = CompetitorPricer(
            policy=config.policy,
            base_prices={
                item.id: item.price for item in by_bakery[Bakery.THE_BAKERY].items
            },
        )

    def rivalries_for(self, menus: Sequence[Menu]) -> list[Rivalry]:
        """Which of The Bakery's items tracks which of grandma's, as these menus stand.

        Recomputed each review rather than fixed at opening: reformulating an
        item moves it on the flavour meters, and what it competes with should
        move with it. Grandma making her parfait savoury should stop The
        Bakery's parfait shadowing it.
        """
        by_bakery = {menu.bakery: menu for menu in menus}
        return find_rivalries(
            by_bakery[Bakery.THE_BAKERY],
            by_bakery[Bakery.GRANDMAS],
            self.config.policy.max_rivalry_distance,
        )

    def player_profile(self, day: int) -> DayProfile:
        """Grandma's profile in force on `day`: the latest one set on or before it."""
        return in_force(self.config.profiles, day) or DayProfile()

    def unit_costs_for(self, day: int, menu: Menu) -> dict[str, float] | None:
        """What each item on `menu` costs its bakery on `day`.

        Costed against that day's ingredient prices and the menu as it stands,
        so a sweetened item (more sugar) or a supplier spike both show up.
        Returns None when the season was given no recipe books; items without
        a recipe are simply left out.
        """
        books = self.recipe_books_for(day)
        book = None if books is None else books.get(menu.bakery)
        if book is None:
            return None

        costs: dict[str, float] = {}
        for item in menu.items:
            try:
                costs[item.id] = book.breakdown(item).total
            except KeyError:
                continue  # No recipe for it; the pricer falls back.
        return costs

    def recipe_books_for(self, day: int) -> Mapping[Bakery, RecipeBook] | None:
        """Recipe books costed at the ingredient prices in force on `day`."""
        prices = in_force(self.config.ingredient_prices, day)
        if self.recipe_books is None or prices is None:
            return self.recipe_books
        return prices.apply(self.recipe_books)

    def run(self) -> SeasonResult:
        records = [record for record, _ in self.iter_days()]
        return SeasonResult(config=self.config, rivalries=self.rivalries, days=records)

    def remembered_prices(
        self, usual: Mapping[str, float], charged: Mapping[str, float]
    ) -> dict[str, float]:
        """Usual prices after a day at `charged`, each moved `price_memory` of the way."""
        memory = self.config.price_memory
        return {
            item_id: round(price + memory * (charged.get(item_id, price) - price), 4)
            for item_id, price in usual.items()
        }

    def iter_days(self) -> Iterator[tuple[DayRecord, DayResult]]:
        """Simulate each day in turn, yielding its record and its full result."""
        history: dict[int, dict[str, float]] = {}
        window: Counter[str] = Counter()
        # The Bakery's standing prices, carried from one day to the next.
        responses: dict[str, float] = {}
        rivalries = self.rivalries
        usual_prices = dict(self.usual_prices)
        habits: Habits = {}

        for day in range(self.config.days):
            menus = self.player_profile(day).apply(self.base_menus)
            by_id = {item.id: item for menu in menus for item in menu.items}
            for item_id, price in responses.items():
                if item_id in by_id:
                    by_id[item_id].price = price

            repricings: list[Repricing] = []
            retargeted: list[Rivalry] | None = None
            if self.config.reactive and self.pricer.is_review_day(day):
                the_bakery = next(m for m in menus if m.bakery is Bakery.THE_BAKERY)
                # The competitor check is also when they notice a reformulation.
                refreshed = self.rivalries_for(menus)
                if _pairs(refreshed) != _pairs(rivalries):
                    rivalries = retargeted = refreshed
                repricings = self.pricer.review(
                    day,
                    the_bakery,
                    rivalries,
                    history,
                    window,
                    self.unit_costs_for(day, the_bakery),
                )
                responses.update({r.item_id: r.new_price for r in repricings})
                window.clear()

            # Record prices only once both sides have moved for the day.
            prices = {item_id: item.price for item_id, item in by_id.items()}
            history[day] = prices

            result = DaySimulator(
                DayConfig(
                    seed=self.config.seed * _DAY_SEED_STRIDE + day,
                    population_seed=self.config.population_seed,
                    population=self.config.population,
                    clock=self.config.clock,
                    choice=self.config.choice,
                    usual_prices=usual_prices,
                    habits=habits,
                ),
                menus,
                self.recipe_books_for(day),
            ).run()
            window.update(result.summary.item_sales)

            record = DayRecord(
                day=day,
                prices=prices,
                usual_prices=usual_prices,
                habit=mean_habit(habits, len(result.customers)),
                summary=result.summary,
                ledger=result.ledger,
                rivalries=retargeted,
                repricings=repricings,
            )
            usual_prices = self.remembered_prices(usual_prices, prices)
            habits = self.config.habits.update(habits, result.events)
            yield record, result
