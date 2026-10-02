"""One generated customer: the fixed traits the choice model scores against."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..core.enums import Allergen, Bakery, FlavorCategory
from ..core.flavor import FlavorProfile


class CustomerProfile(BaseModel):
    """A customer's tastes, constraints and habits.

    These are traits, fixed for the day. Anything that should evolve across
    days (e.g. loyalty earned by a good visit) belongs in separate state.
    """

    id: str
    segment: str

    taste: FlavorProfile = Field(
        default_factory=FlavorProfile,
        description="Ideal point on the flavour meters; categories unused.",
    )
    pickiness: float = Field(
        1.0,
        ge=0.0,
        description="How fast appeal drops as an item drifts from `taste`.",
    )
    category_affinity: dict[FlavorCategory, float] = Field(
        default_factory=dict,
        description="-1 (dislikes) .. +1 (loves). Unlisted categories are 0.",
    )
    allergens: set[Allergen] = Field(default_factory=set)

    price_sensitivity: float = Field(1.0, ge=0.0)
    portion_preference: float = Field(
        0.0,
        ge=-1.0,
        le=1.0,
        description="-1 wants small treats, +1 wants the most food per visit.",
    )
    bakery_bias: dict[Bakery, float] = Field(
        default_factory=dict,
        description="Loyalty / inherent lean per bakery. Unlisted bakeries are 0.",
    )

    visit_probability: float = Field(0.5, ge=0.0, le=1.0)
    arrival_minute: float = Field(
        12 * 60, description="Preferred arrival, minutes since midnight."
    )
    arrival_spread: float = Field(
        30.0, ge=0.0, description="Day-to-day jitter on arrival, in minutes."
    )

    def bias_for(self, bakery: Bakery) -> float:
        return self.bakery_bias.get(bakery, 0.0)

    def affinity_for(self, categories: set[FlavorCategory]) -> float:
        """Mean affinity over an item's flavour tags; 0 for untagged items."""
        if not categories:
            return 0.0
        return sum(self.category_affinity.get(c, 0.0) for c in categories) / len(
            categories
        )
