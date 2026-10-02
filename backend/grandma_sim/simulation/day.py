"""Simulate a whole day at once.

A day's parameters are fixed up front, so the full event log is generated in
one go and the frontend replays it. Separate random streams drive population,
arrivals and choices, so changing e.g. a menu price leaves the same customers
arriving at the same times -- only their decisions move.

`population_seed` fixes who lives in town; `seed` varies the day itself. Keep
the first constant and step the second to simulate the same customers over
consecutive days.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
from pydantic import BaseModel, Field

from ..choice.model import ChoiceConfig, ChoiceModel
from ..core.clock import DayClock
from ..core.enums import Bakery
from ..customers.population import PopulationConfig
from ..customers.presets import default_population
from ..customers.profile import CustomerProfile
from ..menu.costing import RecipeBook
from ..menu.items import Menu
from .events import DaySummary, VisitEvent
from .ledger import DayLedger


def menu_prices(menus: Sequence[Menu]) -> dict[str, float]:
    """Every item's price by id -- e.g. base menus as `DayConfig.usual_prices`."""
    return {item.id: item.price for menu in menus for item in menu.items}


class DayConfig(BaseModel):
    """Everything that defines a day. Same config + same menus = same day."""

    seed: int = Field(0, description="Drives arrivals and choices for this day.")
    population_seed: int = Field(0, description="Drives who the customers are.")
    population: PopulationConfig = Field(default_factory=default_population)
    clock: DayClock = Field(default_factory=DayClock)
    choice: ChoiceConfig = Field(default_factory=ChoiceConfig)
    usual_prices: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "What customers expect each item to cost, by id; prices above this "
            "are penalised as markups. Unlisted items are judged at face value."
        ),
    )


class DayResult(BaseModel):
    config: DayConfig
    menus: list[Menu]
    customers: list[CustomerProfile]
    events: list[VisitEvent]
    summary: DaySummary
    ledger: DayLedger | None = Field(
        None, description="Costs and profit; None when no recipe books were given."
    )


class DaySimulator:
    """Runs one day of customers against a set of competing menus."""

    def __init__(
        self,
        config: DayConfig,
        menus: Sequence[Menu],
        recipe_books: Mapping[Bakery, RecipeBook] | None = None,
    ):
        self.config = config
        self.menus = list(menus)
        self.recipe_books = recipe_books
        self.items = [item for menu in self.menus for item in menu.items]
        self.choice_model = ChoiceModel(config.choice, config.clock, config.usual_prices)

    def run(self) -> DayResult:
        population_rng = np.random.default_rng(self.config.population_seed)
        arrival_rng, choice_rng = (
            np.random.default_rng(seq)
            for seq in np.random.SeedSequence(self.config.seed).spawn(2)
        )
        customers = self.config.population.generate(population_rng)
        events = [
            self._visit(customer, minute, choice_rng)
            for minute, customer in self._arrivals(customers, arrival_rng)
        ]
        return DayResult(
            config=self.config,
            menus=self.menus,
            customers=customers,
            events=events,
            summary=DaySummary.from_events(events),
            ledger=self._ledger(events),
        )

    def _ledger(self, events: Sequence[VisitEvent]) -> DayLedger | None:
        if self.recipe_books is None:
            return None
        return DayLedger.build(events, self.menus, self.recipe_books, self.config.clock)

    def _arrivals(
        self, customers: Sequence[CustomerProfile], rng: np.random.Generator
    ) -> list[tuple[float, CustomerProfile]]:
        """
        Decide who shows up today and when.

        Each customer visits with their own probability, at their preferred
        time plus jitter. Anyone whose arrival lands outside opening hours
        doesn't come, rather than being squeezed in at the door.

        Args:
         customers: The whole population.
         rng: Random stream for arrivals.

        Returns:
         (minute, customer) pairs in time order.
        """
        visit_p = np.array([c.visit_probability for c in customers])
        means = np.array([c.arrival_minute for c in customers])
        spreads = np.array([c.arrival_spread for c in customers])
        visits = rng.random(len(customers)) < visit_p
        minutes = rng.normal(means, spreads)

        arrivals = [
            (float(minute), customer)
            for customer, visiting, minute in zip(customers, visits, minutes)
            if visiting and self.config.clock.is_open(minute)
        ]
        return sorted(arrivals, key=lambda arrival: arrival[0])

    def _visit(
        self, customer: CustomerProfile, minute: float, rng: np.random.Generator
    ) -> VisitEvent:
        clock = self.config.clock
        return VisitEvent(
            minute=minute,
            time=clock.format(minute),
            daypart=clock.daypart_at(minute),
            customer_id=customer.id,
            segment=customer.segment,
            choice=self.choice_model.choose(customer, self.items, minute, rng),
        )
