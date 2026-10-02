"""The simulation as a service: base menus + day profiles -> a simulated day.

Kept free of HTTP so it can be driven from scripts and tests as easily as from
the API.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from ..core.enums import Bakery
from ..menu import store as menu_store
from ..menu.costing import RecipeBook
from ..menu.items import Menu
from ..menu.recipes_seed import recipe_books_by_bakery
from ..menu.seed import build_menus
from ..profiles.overrides import DayProfile
from ..profiles.store import ProfileStore, ScheduledProfile
from ..simulation.day import DayConfig, DayResult, DaySimulator


class SimulationService:
    """Simulates numbered days (1, 2, ...) for one fixed town of customers.

    Every day shares `base_config` -- same population, clock and choice model
    -- and differs only in its seed (the day number) and its menus (the base
    menus with that day's profile applied).
    """

    def __init__(
        self,
        db_path: str | Path = menu_store.DEFAULT_DB_PATH,
        base_config: DayConfig | None = None,
        recipe_books: dict[Bakery, RecipeBook] | None = None,
    ):
        self.db_path = Path(db_path)
        self.base_config = base_config or DayConfig()
        self.recipe_books = recipe_books or recipe_books_by_bakery()
        self.profiles = ProfileStore(self.db_path)
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
        return self.profiles.effective(day)

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

    def menus_for(self, day: int) -> list[Menu]:
        return self.profile_for(day).profile.apply(self.base_menus())

    def simulate(self, day: int) -> DayResult:
        config = self.base_config.model_copy(update={"seed": day})
        return DaySimulator(config, self.menus_for(day), self.recipe_books).run()
