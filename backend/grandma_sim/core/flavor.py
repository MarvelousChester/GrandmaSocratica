"""The flavour meters.

The numeric half of 'what does this taste like'. Menu items carry one, and so
should customer profiles -- same shape on both sides means `distance()` works
for item vs customer (will they buy it?) and item vs item (how close is The
Bakery's knock-off to grandma's original?).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field, field_serializer

from .enums import FlavorCategory

# How much each meter counts when measuring how far apart two things taste.
# Sweetness dominates how a bakery item reads, so it carries the most weight.
_METER_WEIGHTS: dict[str, float] = {
    "sweet_savoury": 1.5,
    "bitterness": 1.0,
    "fruitiness": 1.0,
}

# Worst possible weighted distance, used to normalise `distance()` to 0..1.
# sweet_savoury spans 2.0, the others span 1.0.
_MAX_DISTANCE = math.sqrt(_METER_WEIGHTS["sweet_savoury"] * 2.0**2 + 1.0 + 1.0)


class FlavorProfile(BaseModel):
    """Where something sits on each meter.

    `sweet_savoury` is bipolar: -1 fully savoury, +1 fully sweet, 0 neutral.
    The others run 0..1.
    """

    sweet_savoury: float = Field(0.0, ge=-1.0, le=1.0)
    bitterness: float = Field(0.0, ge=0.0, le=1.0)
    fruitiness: float = Field(0.0, ge=0.0, le=1.0)

    categories: set[FlavorCategory] = Field(default_factory=set)

    @field_serializer("categories")
    def _sorted_categories(self, categories: set[FlavorCategory]) -> list[str]:
        """Sets have no stable order across runs; sort so output is reproducible."""
        return sorted(c.value for c in categories)

    def distance(self, other: FlavorProfile) -> float:
        """0.0 = tastes identical, 1.0 = as far apart as the meters allow.

        Categories are deliberately ignored: two things can both be tagged
        'chocolate' and taste nothing alike. Use `category_overlap()` when you
        want that signal, and weight the two however the matching code likes.
        """
        total = sum(
            weight * (getattr(self, meter) - getattr(other, meter)) ** 2
            for meter, weight in _METER_WEIGHTS.items()
        )
        return math.sqrt(total) / _MAX_DISTANCE

    def category_overlap(self, other: FlavorProfile) -> float:
        """Jaccard overlap of the flavour tags, 0..1. Empty on both sides = 0."""
        if not self.categories and not other.categories:
            return 0.0
        return len(self.categories & other.categories) / len(
            self.categories | other.categories
        )
