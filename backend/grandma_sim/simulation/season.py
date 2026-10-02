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
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from ..choice.model import ChoiceConfig
from ..competition.pricing import CompetitorPricer, PricingPolicy, Repricing
from ..competition.rivalry import Rivalry, find_rivalries
from ..core.clock import DayClock
from ..core.enums import Bakery
from ..customers.population import PopulationConfig
from ..customers.presets import default_population
from ..menu.items import Menu
from ..profiles.overrides import DayProfile
from .day import DayConfig, DaySimulator
from .events import DaySummary

# Keeps per-day seeds far apart so consecutive days don't correlate.
_DAY_SEED_STRIDE = 100_000


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


class DayRecord(BaseModel):
    """One day of the season: what was charged, what sold, what moved."""

    day: int
    prices: dict[str, float] = Field(description="Every item's price that day.")
    summary: DaySummary
    repricings: list[Repricing] = Field(default_factory=list)


class SeasonResult(BaseModel):
    config: SeasonConfig
    rivalries: list[Rivalry]
    days: list[DayRecord]

    def share_series(self, bakery: Bakery) -> list[float]:
        return [record.summary.market_share(bakery) for record in self.days]

    def revenue_series(self, bakery: Bakery) -> list[float]:
        return [record.summary.by_bakery[bakery].revenue for record in self.days]

    def all_repricings(self) -> list[Repricing]:
        return [r for record in self.days for r in record.repricings]


class SeasonSimulator:
    """Days in sequence, with one menu reacting to the other between them."""

    def __init__(self, config: SeasonConfig, base_menus: list[Menu]):
        self.config = config
        self.base_menus = [menu.model_copy(deep=True) for menu in base_menus]

        by_bakery = {menu.bakery: menu for menu in self.base_menus}
        self.rivalries = find_rivalries(
            by_bakery[Bakery.THE_BAKERY],
            by_bakery[Bakery.GRANDMAS],
            config.policy.max_rivalry_distance,
        )
        self.pricer = CompetitorPricer(
            policy=config.policy,
            rivalries=self.rivalries,
            base_prices={
                item.id: item.price for item in by_bakery[Bakery.THE_BAKERY].items
            },
        )

    def player_profile(self, day: int) -> DayProfile:
        """Grandma's profile in force on `day`: the latest one set on or before it."""
        applicable = [d for d in self.config.profiles if d <= day]
        return self.config.profiles[max(applicable)] if applicable else DayProfile()

    def run(self) -> SeasonResult:
        history: dict[int, dict[str, float]] = {}
        window: Counter[str] = Counter()
        # The Bakery's standing prices, carried from one day to the next.
        responses: dict[str, float] = {}
        records: list[DayRecord] = []

        for day in range(self.config.days):
            menus = self.player_profile(day).apply(self.base_menus)
            by_id = {item.id: item for menu in menus for item in menu.items}
            for item_id, price in responses.items():
                if item_id in by_id:
                    by_id[item_id].price = price

            repricings: list[Repricing] = []
            if self.config.reactive and self.pricer.is_review_day(day):
                the_bakery = next(m for m in menus if m.bakery is Bakery.THE_BAKERY)
                repricings = self.pricer.review(day, the_bakery, history, window)
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
                ),
                menus,
            ).run()
            window.update(result.summary.item_sales)

            records.append(
                DayRecord(
                    day=day,
                    prices=prices,
                    summary=result.summary,
                    repricings=repricings,
                )
            )

        return SeasonResult(config=self.config, rivalries=self.rivalries, days=records)
