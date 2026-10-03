"""The Bakery's repricing policy.

A corporate chain doesn't watch a neighbour's menu board in real time and it
doesn't reprice overnight, so three separate delays sit between grandma
changing a price and The Bakery answering:

  * `observation_lag_days` -- they act on the price they last *saw*, not
    today's. Competitor checks happen on a round, not continuously.
  * `review_every_days` -- even once noticed, prices only move on review day.
    Approvals, reprinted boards, POS updates.
  * `adjustment_rate` -- they move part of the way to their target, not all of
    it. Jumping straight there makes the two shops oscillate; easing in
    converges and reads like a competitor feeling the market out.

They watch three things: grandma's posted prices (stale, because of the lag),
their own till (current -- it's their own data) and their own costs. Share
decides whether they bother; chains that are winning don't cut, they harvest.

Cost decides how far they can go. The floor under every price is what the item
costs them to make today, so they will not undercut themselves into a loss --
and when an ingredient price jumps, they raise to stay above it whether or not
they are winning. That floor moves with the recipe, so sweetening an item (more
sugar, more cost) lifts it too.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel, Field

from ..menu.items import Menu, MenuItem
from .rivalry import Rivalry

# Below this, a move isn't worth reprinting the board for.
MIN_PRICE_MOVE = 0.05


class Reason(str, Enum):
    UNDERCUT = "undercut"
    FOLLOW_UP = "follow_up"
    HARVEST = "harvest"
    COST_FLOOR = "cost_floor"


class PricingPolicy(BaseModel):
    """How aggressive The Bakery is, and how slowly it moves."""

    undercut: float = Field(
        0.12, ge=0.0, lt=1.0, description="Target price gap below the rival item."
    )
    adjustment_rate: float = Field(
        0.4, gt=0.0, le=1.0, description="Fraction of the gap closed each review."
    )
    review_every_days: int = Field(7, ge=1)
    observation_lag_days: int = Field(4, ge=0)

    losing_below: float = Field(
        0.50, ge=0.0, le=1.0, description="Share of the pair under which they cut."
    )
    harvesting_above: float = Field(
        0.65, ge=0.0, le=1.0, description="Share over which they raise instead."
    )
    harvest_step: float = Field(
        0.05, ge=0.0, description="Price rise attempted while comfortably ahead."
    )

    min_margin_pct: float = Field(
        0.10,
        ge=0.0,
        lt=1.0,
        description="Gross margin they refuse to go under. 0.0 = break even exactly.",
    )
    price_floor_pct: float = Field(
        0.75,
        gt=0.0,
        description="Fallback floor, as a fraction of the opening price, for items "
        "with no recipe to cost.",
    )
    price_ceiling_pct: float = Field(
        1.25, gt=0.0, description="Never above this fraction of the opening price."
    )
    max_rivalry_distance: float = Field(
        0.25, gt=0.0, description="Taste gap beyond which two items aren't substitutes."
    )
    snap_endings: list[float] = Field(
        default_factory=lambda: [0.95, 0.49],
        description="Menu boards end in round numbers. Empty disables snapping.",
    )


class Repricing(BaseModel):
    """One price change, with the evidence behind it."""

    day: int
    item_id: str
    item_name: str
    old_price: float
    new_price: float
    reason: Reason
    rival_name: str
    observed_rival_price: float
    observed_on_day: int = Field(description="Which day's menu board they acted on.")
    observed_share: float = Field(description="Their share of the pair since last review.")
    unit_cost: float | None = Field(
        None, description="What the item cost them to make that day, if known."
    )
    floor: float = Field(description="The least they would charge, given that cost.")

    @property
    def change(self) -> float:
        return self.new_price - self.old_price


def snap(price: float, endings: list[float], floor: float = 0.0) -> float:
    """Round a price to the nearest acceptable menu-board ending.

    Never rounds below `floor`: a price that is break-even to the cent must not
    become a loss just to end in .95.
    """
    if not endings:
        return round(max(price, floor), 2)
    whole = math.floor(price)
    candidates = [
        w + ending
        for w in (whole - 1, whole, whole + 1, whole + 2)
        for ending in endings
    ]
    allowed = [c for c in candidates if c > 0 and c >= floor]
    if not allowed:
        return round(max(price, floor), 2)
    return min(allowed, key=lambda c: abs(c - price))


class CompetitorPricer:
    """Reprices one menu in response to another, on a fixed review cycle."""

    def __init__(
        self, policy: PricingPolicy, rivalries: list[Rivalry], base_prices: dict[str, float]
    ):
        self.policy = policy
        self.rivalries = rivalries
        self.base_prices = base_prices

    def floor_for(
        self, item: MenuItem, unit_costs: Mapping[str, float] | None
    ) -> float:
        """The least they will charge: what it costs, plus their minimum margin.

        Falls back to a flat fraction of the opening price for an item with no
        costed recipe -- a crude floor, but better than none.
        """
        cost = (unit_costs or {}).get(item.id)
        if cost is None:
            return self.base_prices[item.id] * self.policy.price_floor_pct
        return cost / (1.0 - self.policy.min_margin_pct)

    def _both_on_sale(
        self, rivalry: Rivalry, menu: Menu, history: dict[int, dict[str, float]], day: int
    ) -> bool:
        if not any(item.id == rivalry.watcher_id for item in menu.items):
            return False
        return rivalry.rival_id in history.get(self.observed_day(day, history), {})

    def is_review_day(self, day: int) -> bool:
        """Day 0 is opening, so the first review lands one full cycle in."""
        return day > 0 and day % self.policy.review_every_days == 0

    def observed_day(self, day: int, history: dict[int, dict[str, float]]) -> int:
        """Which day's menu board The Bakery is acting on today.

        Competitor price checks happen on a round, so they answer the price
        they last saw rather than today's. Before the lag has elapsed there is
        only opening-day information to go on.
        """
        seen_on = max(day - self.policy.observation_lag_days, 0)
        available = [d for d in history if d <= seen_on]
        return max(available) if available else min(history)

    def review(
        self,
        day: int,
        menu: Menu,
        history: dict[int, dict[str, float]],
        window_sales: Counter[str],
        unit_costs: Mapping[str, float] | None = None,
    ) -> list[Repricing]:
        """
        Reprice every tracked item, in place, and report what changed.

        Args:
         day: Today's index in the season.
         menu: The Bakery's menu, mutated with the new prices.
         history: day -> {item_id: price}, every price ever posted.
         window_sales: Units sold per item since the last review, both menus.
         unit_costs: What each of their items costs to make today. Items left
          out fall back to `price_floor_pct` of their opening price.

        Returns:
         One `Repricing` per item that actually moved.
        """
        changes: list[Repricing] = []
        for rivalry in self.rivalries:
            # A day profile can pull either item off the menu; nothing to do.
            if not self._both_on_sale(rivalry, menu, history, day):
                continue
            item = menu.get(rivalry.watcher_id)
            sold = window_sales[rivalry.watcher_id]
            rival_sold = window_sales[rivalry.rival_id]
            if sold + rival_sold == 0:
                continue  # Nobody bought either; no signal to act on.

            share = sold / (sold + rival_sold)
            observed_day = self.observed_day(day, history)
            rival_price = history[observed_day][rivalry.rival_id]

            cost = (unit_costs or {}).get(item.id)
            floor = self.floor_for(item, unit_costs)

            if item.price < floor:
                # Selling under cost outranks anything share is saying.
                target, reason = floor, Reason.COST_FLOOR
            elif share < self.policy.losing_below:
                target = rival_price * (1.0 - self.policy.undercut)
                reason = Reason.UNDERCUT if target < item.price else Reason.FOLLOW_UP
            elif share > self.policy.harvesting_above:
                target = item.price * (1.0 + self.policy.harvest_step)
                reason = Reason.HARVEST
            else:
                continue  # Holding their own; not worth the disruption.

            # A rise off the floor isn't eased in -- nobody phases out a loss.
            eased = (
                target
                if reason is Reason.COST_FLOOR
                else item.price + self.policy.adjustment_rate * (target - item.price)
            )
            ceiling = self.base_prices[item.id] * self.policy.price_ceiling_pct
            # Floor applied last: cost beats the ceiling when ingredients spike.
            bounded = max(min(eased, ceiling), floor)
            new_price = snap(bounded, self.policy.snap_endings, floor=floor)
            if abs(new_price - item.price) < MIN_PRICE_MOVE:
                continue

            changes.append(
                Repricing(
                    day=day,
                    item_id=item.id,
                    item_name=item.name,
                    old_price=item.price,
                    new_price=new_price,
                    reason=reason,
                    rival_name=rivalry.rival_name,
                    observed_rival_price=rival_price,
                    observed_on_day=observed_day,
                    observed_share=share,
                    unit_cost=cost,
                    floor=floor,
                )
            )
            item.price = new_price

        return changes
