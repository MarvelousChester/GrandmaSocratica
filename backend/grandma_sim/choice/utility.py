"""How much one customer wants one item at one moment.

The score is a sum of named terms, kept separate in `UtilityBreakdown` so the
frontend can explain a choice ("cheaper, but too sweet for them").
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from pydantic import BaseModel, Field, computed_field

from ..core.clock import DayClock
from ..customers.profile import CustomerProfile
from ..menu.items import MenuItem

# Free items are allowed on the menu; floor the price so log() stays finite.
_MIN_PRICE = 0.01

# Caps the markup exponent so absurd prices give a huge penalty, not an overflow.
_MAX_MARKUP_EXPONENT = 50.0


def markup_penalty(markup: float, tolerance: float) -> float:
    """
    How much paying `markup` over the usual price hurts, before weighting.

    Exponential for rises: tolerance * (e^(markup / tolerance) - 1). A small
    rise costs roughly its own size, and every further `tolerance` above the
    usual price multiplies the cost by e -- so 2% barely registers but 30% is
    a dealbreaker. Discounts are linear (negative markup, negative penalty):
    a cut helps, but never explosively.

    Args:
     markup: Price relative to the usual price, minus 1 (0.3 = 30% dearer).
     tolerance: Markup per e-fold of the penalty.

    Returns:
     The penalty; negative for discounts.
    """
    if markup <= 0.0:
        return markup
    return tolerance * math.expm1(min(markup / tolerance, _MAX_MARKUP_EXPONENT))


class UtilityWeights(BaseModel):
    """Global scale of each utility term, shared by every customer."""

    taste: float = 3.0
    category: float = 1.0
    daypart: float = 2.0
    price: float = Field(
        1.0, description="How much dearer items lose against cheaper ones, at usual prices."
    )
    markup: float = Field(
        0.5, description="How much an item loses for costing more than usual."
    )
    markup_tolerance: float = Field(
        0.07,
        gt=0.0,
        description="Markup per e-fold of the markup penalty; smaller = touchier.",
    )
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
    markup: float = 0.0
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
            + self.markup
            + self.portion
            + self.bakery
        )


class UtilityModel:
    """Scores items for customers under a fixed set of weights and clock.

    `usual_prices` are what customers expect each item to cost (by item id);
    an item without one is judged against its own price, i.e. no markup.
    """

    def __init__(
        self,
        weights: UtilityWeights,
        clock: DayClock,
        usual_prices: Mapping[str, float] | None = None,
    ):
        self.weights = weights
        self.clock = clock
        self.usual_prices = usual_prices or {}

    def markup(self, item: MenuItem) -> float:
        """Price relative to the usual price, minus 1 (0.3 = 30% dearer)."""
        usual = self.usual_prices.get(item.id, item.price)
        return max(item.price, _MIN_PRICE) / max(usual, _MIN_PRICE) - 1.0

    def daypart_appeal(self, item: MenuItem, minute: float) -> float:
        """The item's daypart pull at `minute`, blended across dayparts."""
        mix = self.clock.daypart_mix(minute)
        return sum(weight * item.appeal_at(dp) for dp, weight in mix.items())

    def score(
        self, customer: CustomerProfile, item: MenuItem, minute: float
    ) -> UtilityBreakdown:
        """
        Break down how much `customer` wants `item` at `minute`.

        Price counts twice: `price` compares the item's level to the global
        reference on a log scale (dear items lose to cheap ones), and `markup`
        compares it to the item's usual price (see `markup_penalty`). Portion
        is log-scaled against its reference too. Daypart appeal is centred on
        0.5, the item default, so a neutral item neither gains nor loses.

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
            markup=-w.markup
            * customer.price_sensitivity
            * markup_penalty(self.markup(item), w.markup_tolerance),
            portion=w.portion
            * customer.portion_preference
            * math.log(item.portion_size_g / w.reference_portion_g),
            bakery=w.bakery * customer.bias_for(item.bakery),
        )
