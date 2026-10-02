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

They watch two things: grandma's posted prices (stale, because of the lag)
and their own till (current -- it's their own data). Share is what decides
whether they bother. Chains that are winning don't cut, they harvest.
"""

from __future__ import annotations

import math
from collections import Counter
from enum import Enum

from pydantic import BaseModel, Field

from ..menu.items import Menu
from .rivalry import Rivalry

# Below this, a move isn't worth reprinting the board for.
MIN_PRICE_MOVE = 0.05


class Reason(str, Enum):
    UNDERCUT = "undercut"
    FOLLOW_UP = "follow_up"
    HARVEST = "harvest"


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

    price_floor_pct: float = Field(
        0.75, gt=0.0, description="Never below this fraction of the opening price."
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

    @property
    def change(self) -> float:
        return self.new_price - self.old_price


def snap(price: float, endings: list[float]) -> float:
    """Round a price to the nearest acceptable menu-board ending."""
    if not endings:
        return round(price, 2)
    whole = math.floor(price)
    candidates = [
        w + ending for w in (whole - 1, whole, whole + 1) for ending in endings
    ]
    return min((c for c in candidates if c > 0), key=lambda c: abs(c - price))


class CompetitorPricer:
    """Reprices one menu in response to another, on a fixed review cycle."""

    def __init__(
        self, policy: PricingPolicy, rivalries: list[Rivalry], base_prices: dict[str, float]
    ):
        self.policy = policy
        self.rivalries = rivalries
        self.base_prices = base_prices

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
    ) -> list[Repricing]:
        """
        Reprice every tracked item, in place, and report what changed.

        Args:
         day: Today's index in the season.
         menu: The Bakery's menu, mutated with the new prices.
         history: day -> {item_id: price}, every price ever posted.
         window_sales: Units sold per item since the last review, both menus.

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

            if share < self.policy.losing_below:
                target = rival_price * (1.0 - self.policy.undercut)
                reason = Reason.UNDERCUT if target < item.price else Reason.FOLLOW_UP
            elif share > self.policy.harvesting_above:
                target = item.price * (1.0 + self.policy.harvest_step)
                reason = Reason.HARVEST
            else:
                continue  # Holding their own; not worth the disruption.

            base = self.base_prices[item.id]
            eased = item.price + self.policy.adjustment_rate * (target - item.price)
            bounded = min(
                max(eased, base * self.policy.price_floor_pct),
                base * self.policy.price_ceiling_pct,
            )
            new_price = snap(bounded, self.policy.snap_endings)
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
                )
            )
            item.price = new_price

        return changes
