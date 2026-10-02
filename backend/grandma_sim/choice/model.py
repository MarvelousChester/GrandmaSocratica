"""The customer decision: one item from either menu, or walk away.

A multinomial logit over every allergen-safe item plus a 'buy nothing' option.
Probabilities are a softmax of utility / temperature: low temperature means
customers reliably take their best option, high temperature means noisier,
more impulsive choices.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, Field, computed_field

from ..core.clock import DayClock
from ..core.enums import Bakery
from ..customers.profile import CustomerProfile
from ..menu.items import MenuItem
from .utility import UtilityBreakdown, UtilityModel, UtilityWeights


class ChoiceConfig(BaseModel):
    weights: UtilityWeights = Field(default_factory=UtilityWeights)
    temperature: float = Field(1.0, gt=0.0)
    no_purchase_utility: float = Field(
        1.0, description="Utility of leaving empty-handed; raise it to lose sales."
    )


class ScoredOption(BaseModel):
    """One alternative a customer weighed. `item` is None for 'buy nothing'."""

    item: MenuItem | None
    utility: float
    probability: float
    breakdown: UtilityBreakdown | None = None


class Choice(BaseModel):
    """What a customer ended up doing, plus why."""

    item_id: str | None = None
    item_name: str | None = None
    bakery: Bakery | None = None
    price: float = 0.0
    probability: float = Field(description="Chance this outcome had of happening.")
    breakdown: UtilityBreakdown | None = None

    @computed_field
    @property
    def purchased(self) -> bool:
        return self.item_id is not None

    @classmethod
    def from_option(cls, option: ScoredOption) -> Choice:
        if option.item is None:
            return cls(probability=option.probability)
        return cls(
            item_id=option.item.id,
            item_name=option.item.name,
            bakery=option.item.bakery,
            price=option.item.price,
            probability=option.probability,
            breakdown=option.breakdown,
        )


class ChoiceModel:
    """Turns utilities into probabilities and samples a decision."""

    def __init__(self, config: ChoiceConfig, clock: DayClock):
        self.config = config
        self.utility = UtilityModel(config.weights, clock)

    def options(
        self, customer: CustomerProfile, items: Sequence[MenuItem], minute: float
    ) -> list[ScoredOption]:
        """
        Score every alternative open to `customer` at `minute`.

        Items the customer is allergic to are excluded outright rather than
        penalised, so they can never be picked.

        Args:
         customer: Who is choosing.
         items: Everything on offer, across both bakeries.
         minute: Minutes since midnight.

        Returns:
         'Buy nothing' first, then each safe item, with probabilities summing
         to 1.
        """
        safe = [item for item in items if item.safe_for(customer.allergens)]
        breakdowns = [self.utility.score(customer, item, minute) for item in safe]
        utilities = np.array(
            [self.config.no_purchase_utility] + [b.total for b in breakdowns]
        )

        logits = utilities / self.config.temperature
        weights = np.exp(logits - logits.max())
        probabilities = weights / weights.sum()

        options = [
            ScoredOption(item=None, utility=utilities[0], probability=probabilities[0])
        ]
        options.extend(
            ScoredOption(item=item, utility=u, probability=p, breakdown=b)
            for item, u, p, b in zip(safe, utilities[1:], probabilities[1:], breakdowns)
        )
        return options

    def choose(
        self,
        customer: CustomerProfile,
        items: Sequence[MenuItem],
        minute: float,
        rng: np.random.Generator,
    ) -> Choice:
        options = self.options(customer, items, minute)
        picked = rng.choice(len(options), p=[o.probability for o in options])
        return Choice.from_option(options[picked])
