"""How much one customer wants one item at one moment.

The score is a sum of named terms, kept separate in `UtilityBreakdown` so the
frontend can explain a choice ("cheaper, but too sweet for them").
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field, computed_field

from ..core.clock import DayClock
from ..customers.profile import CustomerProfile
from ..menu.items import MenuItem

# Free items are allowed on the menu; floor the price so log() stays finite.
_MIN_PRICE = 0.01


class UtilityWeights(BaseModel):
    """Global scale of each utility term, shared by every customer."""

    taste: float = 3.0
    category: float = 1.0
    daypart: float = 2.0
    price: float = 1.0
    portion: float = 0.5
    bakery: float = 1.0
    reference_price: float = Field(
        5.0, gt=0.0, description="Price that is neither cheap nor dear."
    )
    reference_portion_g: float = Field(
        200.0, gt=0.0, description="Portion that is neither small nor big."
    )


class UtilityBreakdown(BaseModel):
    """Each term's contribution to the score; `total` is their sum."""

    taste: float
    category: float
    daypart: float
    price: float
    portion: float
    bakery: float

    @computed_field
    @property
    def total(self) -> float:
        return (
            self.taste
            + self.category
            + self.daypart
            + self.price
            + self.portion
            + self.bakery
        )


class UtilityModel:
    """Scores items for customers under a fixed set of weights and clock."""

    def __init__(self, weights: UtilityWeights, clock: DayClock):
        self.weights = weights
        self.clock = clock

    def daypart_appeal(self, item: MenuItem, minute: float) -> float:
        """The item's daypart pull at `minute`, blended across dayparts."""
        mix = self.clock.daypart_mix(minute)
        return sum(weight * item.appeal_at(dp) for dp, weight in mix.items())

    def score(
        self, customer: CustomerProfile, item: MenuItem, minute: float
    ) -> UtilityBreakdown:
        """
        Break down how much `customer` wants `item` at `minute`.

        Price and portion enter on a log scale relative to the reference
        values, so doubling a price costs the same utility at any level.
        Daypart appeal is centred on 0.5, the item default, so a neutral item
        neither gains nor loses.

        Args:
         customer: Who is choosing.
         item: What they are considering.
         minute: Minutes since midnight.

        Returns:
         The per-term utility contributions.
        """
        w = self.weights
        distance = customer.taste.distance(item.flavor)
        return UtilityBreakdown(
            taste=w.taste * (1.0 - customer.pickiness * distance),
            category=w.category * customer.affinity_for(item.flavor.categories),
            daypart=w.daypart * (self.daypart_appeal(item, minute) - 0.5),
            price=-w.price
            * customer.price_sensitivity
            * math.log(max(item.price, _MIN_PRICE) / w.reference_price),
            portion=w.portion
            * customer.portion_preference
            * math.log(item.portion_size_g / w.reference_portion_g),
            bakery=w.bakery * customer.bias_for(item.bakery),
        )
