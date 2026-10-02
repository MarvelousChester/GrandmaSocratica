"""Simulate a whole day at once.

A day's parameters are fixed up front, so the full event log is generated in
one go and the frontend replays it. Separate random streams drive population,
arrivals and choices, so changing e.g. a menu price leaves the same customers
arriving at the same times -- only their decisions move.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, Field

from ..choice.model import ChoiceConfig, ChoiceModel
from ..core.clock import DayClock
from ..customers.population import PopulationConfig
from ..customers.presets import default_population
from ..customers.profile import CustomerProfile
from ..menu.items import Menu
from .events import DaySummary, VisitEvent


class DayConfig(BaseModel):
    """Everything that defines a day. Same config + same menus = same day."""

    seed: int = 0
    population: PopulationConfig = Field(default_factory=default_population)
    clock: DayClock = Field(default_factory=DayClock)
    choice: ChoiceConfig = Field(default_factory=ChoiceConfig)


class DayResult(BaseModel):
    config: DayConfig
    customers: list[CustomerProfile]
    events: list[VisitEvent]
    summary: DaySummary


class DaySimulator:
    """Runs one day of customers against a set of competing menus."""

    def __init__(self, config: DayConfig, menus: Sequence[Menu]):
        self.config = config
        self.items = [item for menu in menus for item in menu.items]
        self.choice_model = ChoiceModel(config.choice, config.clock)

    def run(self) -> DayResult:
        population_rng, arrival_rng, choice_rng = (
            np.random.default_rng(seq)
            for seq in np.random.SeedSequence(self.config.seed).spawn(3)
        )
        customers = self.config.population.generate(population_rng)
        events = [
            self._visit(customer, minute, choice_rng)
            for minute, customer in self._arrivals(customers, arrival_rng)
        ]
        return DayResult(
            config=self.config,
            customers=customers,
            events=events,
            summary=DaySummary.from_events(events),
        )

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
