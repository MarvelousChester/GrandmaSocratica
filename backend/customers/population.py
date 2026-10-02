"""Population generation: a mixture of customer segments.

Each segment (commuter, student, ...) carries its own distributions, so traits
correlate the way real crowds do rather than averaging into one bland blob.
Everything here is plain config -- load it from JSON, tweak it, re-run.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from ..core.enums import Allergen, Bakery, FlavorCategory
from ..core.flavor import FlavorProfile
from .distributions import Beta, Constant, DistributionSpec, Normal
from .profile import CustomerProfile


class SegmentConfig(BaseModel):
    """Generation parameters for one archetype of customer."""

    name: str
    share: float = Field(gt=0.0, description="Relative weight in the population.")

    sweet_savoury: DistributionSpec = Normal(mean=0.3, sd=0.4, low=-1.0, high=1.0)
    bitterness: DistributionSpec = Beta(a=2.0, b=5.0)
    fruitiness: DistributionSpec = Beta(a=2.0, b=3.0)
    pickiness: DistributionSpec = Normal(mean=2.0, sd=0.5, low=0.0)
    category_affinity: dict[FlavorCategory, DistributionSpec] = Field(
        default_factory=dict
    )
    allergen_prevalence: dict[Allergen, float] = Field(
        default_factory=dict, description="Probability of avoiding each allergen."
    )

    price_sensitivity: DistributionSpec = Normal(mean=1.0, sd=0.3, low=0.0)
    portion_preference: DistributionSpec = Normal(mean=0.0, sd=0.4, low=-1.0, high=1.0)
    bakery_bias: dict[Bakery, DistributionSpec] = Field(default_factory=dict)

    visit_probability: DistributionSpec = Beta(a=2.0, b=3.0)
    arrival_minute: DistributionSpec = Normal(mean=12 * 60, sd=120)
    arrival_spread: DistributionSpec = Constant(value=30.0)

    def sample(
        self, rng: np.random.Generator, size: int, id_offset: int = 0
    ) -> list[CustomerProfile]:
        """
        Draw `size` customers from this segment.

        Args:
         rng: Random generator to draw from.
         size: Number of customers to generate.
         id_offset: Starting index for customer ids, so ids stay unique
          across segments.

        Returns:
         The generated customer profiles.
        """
        sweet = self.sweet_savoury.sample(rng, size)
        bitter = self.bitterness.sample(rng, size)
        fruity = self.fruitiness.sample(rng, size)
        picky = self.pickiness.sample(rng, size)
        price = self.price_sensitivity.sample(rng, size)
        portion = self.portion_preference.sample(rng, size)
        visit = self.visit_probability.sample(rng, size)
        arrival = self.arrival_minute.sample(rng, size)
        spread = self.arrival_spread.sample(rng, size)
        affinity = {c: d.sample(rng, size) for c, d in self.category_affinity.items()}
        bias = {b: d.sample(rng, size) for b, d in self.bakery_bias.items()}
        avoids = {a: rng.random(size) < p for a, p in self.allergen_prevalence.items()}

        # Assemble one profile per row of the sampled columns.
        return [
            CustomerProfile(
                id=f"c{id_offset + i:05d}",
                segment=self.name,
                taste=FlavorProfile(
                    sweet_savoury=sweet[i], bitterness=bitter[i], fruitiness=fruity[i]
                ),
                pickiness=picky[i],
                category_affinity={c: float(v[i]) for c, v in affinity.items()},
                allergens={a for a, hit in avoids.items() if hit[i]},
                price_sensitivity=price[i],
                portion_preference=portion[i],
                bakery_bias={b: float(v[i]) for b, v in bias.items()},
                visit_probability=visit[i],
                arrival_minute=arrival[i],
                arrival_spread=max(spread[i], 0.0),
            )
            for i in range(size)
        ]


class PopulationConfig(BaseModel):
    """The whole customer base: how many people, split across which segments."""

    size: int = Field(gt=0)
    segments: list[SegmentConfig] = Field(min_length=1)

    @classmethod
    def from_json(cls, path: str | Path) -> PopulationConfig:
        return cls.model_validate_json(Path(path).read_text())

    def generate(self, rng: np.random.Generator) -> list[CustomerProfile]:
        """Split `size` across segments by share, then sample each segment."""
        shares = np.array([s.share for s in self.segments], dtype=float)
        counts = rng.multinomial(self.size, shares / shares.sum())

        customers: list[CustomerProfile] = []
        for segment, count in zip(self.segments, counts):
            customers.extend(segment.sample(rng, int(count), id_offset=len(customers)))
        return customers
