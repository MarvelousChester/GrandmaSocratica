"""Per-day ingredient price changes, layered over each bakery's pantry.

Separate from `DayProfile` on purpose: menu changes are the player's call,
ingredient prices are the market's (a butter shortage, a new supplier), and
each carries forward on its own schedule without one wiping the other.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from pydantic import BaseModel, Field

from ..core.enums import Bakery
from ..menu.costing import RecipeBook

NonNegative = Annotated[float, Field(ge=0.0)]


class IngredientPrices(BaseModel):
    """Ingredient price changes for a day. Unlisted ingredients keep their price."""

    multipliers: dict[str, NonNegative] = Field(
        default_factory=dict,
        description="Market-wide: scales an ingredient's price at every bakery (1.5 = +50%).",
    )
    prices: dict[Bakery, dict[str, NonNegative]] = Field(
        default_factory=dict,
        description="One bakery's price per kg, set outright. Wins over a multiplier.",
    )

    def apply(self, books: Mapping[Bakery, RecipeBook]) -> dict[Bakery, RecipeBook]:
        """
        Reprice each bakery's pantry, leaving recipes untouched.

        Args:
         books: Each bakery's base recipe book.

        Returns:
         New recipe books with the day's ingredient prices.

        Raises:
         ValueError: If an ingredient or bakery isn't in the given books.
        """
        known = {i for book in books.values() for i in book.pantry.ingredients}
        unknown = sorted(set(self.multipliers) - known)
        for bakery, prices in self.prices.items():
            if bakery not in books:
                raise ValueError(f"no recipe book for bakery {bakery.value!r}")
            unknown += sorted(set(prices) - set(books[bakery].pantry.ingredients))
        if unknown:
            raise ValueError(f"no ingredient with id(s): {', '.join(unknown)}")

        result = {}
        for bakery, book in books.items():
            pantry = book.pantry
            for ingredient_id, factor in self.multipliers.items():
                if ingredient_id in pantry.ingredients:
                    price = pantry.price_per_kg(ingredient_id) * factor
                    pantry = pantry.with_price(ingredient_id, price)
            for ingredient_id, price in self.prices.get(bakery, {}).items():
                pantry = pantry.with_price(ingredient_id, price)
            result[bakery] = book.model_copy(update={"pantry": pantry})
        return result
