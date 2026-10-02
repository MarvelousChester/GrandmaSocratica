"""Distribution specs: the knobs a population config is made of.

Each spec is plain data (so configs round-trip through JSON) that knows how to
draw from itself. The `kind` field picks the class when loading from JSON:

    {"kind": "normal", "mean": 0.3, "sd": 0.2, "low": -1, "high": 1}
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

import numpy as np
from pydantic import BaseModel, Field, model_validator


class Distribution(BaseModel):
    """Base class. Subclasses draw `size` values as a float array."""

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        raise NotImplementedError


class Constant(Distribution):
    kind: Literal["constant"] = "constant"
    value: float

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        return np.full(size, self.value, dtype=float)


class Uniform(Distribution):
    kind: Literal["uniform"] = "uniform"
    low: float
    high: float

    @model_validator(mode="after")
    def _check_bounds(self) -> Uniform:
        if self.high < self.low:
            raise ValueError("high must be >= low")
        return self

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        return rng.uniform(self.low, self.high, size)


class Normal(Distribution):
    """Gaussian, optionally clipped to [low, high] to respect a meter's range."""

    kind: Literal["normal"] = "normal"
    mean: float
    sd: float = Field(ge=0.0)
    low: float | None = None
    high: float | None = None

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        values = rng.normal(self.mean, self.sd, size)
        if self.low is not None or self.high is not None:
            values = np.clip(values, self.low, self.high)
        return values


class Beta(Distribution):
    """Beta(a, b) rescaled onto [low, high]. Good for bounded, skewed traits."""

    kind: Literal["beta"] = "beta"
    a: float = Field(gt=0.0)
    b: float = Field(gt=0.0)
    low: float = 0.0
    high: float = 1.0

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        return self.low + (self.high - self.low) * rng.beta(self.a, self.b, size)


DistributionSpec = Annotated[
    Union[Constant, Uniform, Normal, Beta], Field(discriminator="kind")
]
