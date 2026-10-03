"""What an item costs to make, as opposed to what it sells for.

`MenuItem.price` is the shelf price the customer sees. The cost here is
derived from what is in the item: a recipe is a set of ingredient shares
(by mass, summing to 1.0), a pantry holds each ingredient's price per kg, and
cost = portion weight x the share-weighted price of its ingredients.

    0.4 egg + 0.4 wheat + 0.1 sugar  ->  0.4*egg + 0.4*wheat + 0.1*sugar  per kg

Pantries are per bakery, so the same recipe costs different amounts at
grandma's (premium ingredients) and The Bakery (bulk ingredients).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .items import MenuItem


class Ingredient(BaseModel):
    id: str
    name: str
    price_per_kg: float = Field(ge=0.0)


class Pantry(BaseModel):
    """One bakery's ingredient price list."""

    ingredients: dict[str, Ingredient] = Field(default_factory=dict)

    def add(self, *ingredients: Ingredient) -> Pantry:
        for ing in ingredients:
            self.ingredients[ing.id] = ing
        return self

    def price_per_kg(self, ingredient_id: str) -> float:
        try:
            return self.ingredients[ingredient_id].price_per_kg
        except KeyError:
            raise KeyError(f"no ingredient {ingredient_id!r} in the pantry") from None

    def scaled(self, factor: float) -> Pantry:
        """Same ingredients at `factor` x the price (premium > 1, bulk < 1)."""
        return Pantry(
            ingredients={
                i: ing.model_copy(update={"price_per_kg": ing.price_per_kg * factor})
                for i, ing in self.ingredients.items()
            }
        )

    def with_price(self, ingredient_id: str, price_per_kg: float) -> Pantry:
        """Copy with one price changed -- model a butter price spike."""
        ing = self.ingredients[ingredient_id]
        updated = dict(self.ingredients)
        updated[ingredient_id] = ing.model_copy(update={"price_per_kg": price_per_kg})
        return Pantry(ingredients=updated)


class RecipeLine(BaseModel):
    ingredient_id: str
    share: float = Field(gt=0.0, le=1.0, description="Fraction of the item's mass.")


class CostLine(BaseModel):
    ingredient_id: str
    grams: float
    cost: float


class CostBreakdown(BaseModel):
    item_id: str
    lines: list[CostLine]

    @property
    def total(self) -> float:
        return sum(line.cost for line in self.lines)

    def margin(self, item: MenuItem) -> float:
        """Profit per unit sold at the item's current shelf price."""
        return item.price - self.total

    def margin_pct(self, item: MenuItem) -> float:
        """Margin as a fraction of price (0.6 = 60% gross margin)."""
        return self.margin(item) / item.price if item.price else 0.0

    def biggest_cost(self) -> CostLine | None:
        return max(self.lines, key=lambda line: line.cost, default=None)


class Recipe(BaseModel):
    """What one menu item is made of, as shares of its mass.

    The listed shares are the recipe at `base_sweetness`. Sweetening or
    savouring the item scales only the `sweeteners` by (1 + s) / (1 + base);
    every other ingredient keeps its grams. Sweeter is extra sugar on top, so it
    always costs more (and a portion weighs slightly more than `portion_size_g`).
    A recipe with no sweeteners costs the same at any sweetness.
    """

    item_id: str
    lines: list[RecipeLine]
    base_sweetness: float = Field(0.0, gt=-1.0, le=1.0)
    sweeteners: frozenset[str] = frozenset({"sugar", "maple_syrup"})

    @model_validator(mode="after")
    def _shares_sum_to_one(self) -> Recipe:
        total = sum(line.share for line in self.lines)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"recipe {self.item_id!r} shares sum to {total:.3f}, not 1.0")
        return self

    def sweetener_factor(self, sweetness: float) -> float:
        """Multiplier on the sweetener grams at `sweetness` (1.0 at the base)."""
        return (1.0 + sweetness) / (1.0 + self.base_sweetness)

    def cost_per_kg(self, pantry: Pantry, sweetness: float | None = None) -> float:
        """Cost per kg of the base recipe's mass, with sweeteners scaled."""
        f = self.sweetener_factor(self.base_sweetness if sweetness is None else sweetness)
        return sum(
            line.share * (f if line.ingredient_id in self.sweeteners else 1.0)
            * pantry.price_per_kg(line.ingredient_id)
            for line in self.lines
        )

    def breakdown(self, item: MenuItem, pantry: Pantry) -> CostBreakdown:
        factor = self.sweetener_factor(item.flavor.sweet_savoury)
        lines = []
        for line in self.lines:
            scale = factor if line.ingredient_id in self.sweeteners else 1.0
            grams = item.portion_size_g * line.share * scale
            lines.append(
                CostLine(
                    ingredient_id=line.ingredient_id,
                    grams=grams,
                    cost=grams / 1000 * pantry.price_per_kg(line.ingredient_id),
                )
            )
        return CostBreakdown(item_id=item.id, lines=lines)

    def unit_cost(self, item: MenuItem, pantry: Pantry) -> float:
        """Cost to make one portion of `item`."""
        return self.breakdown(item, pantry).total


class RecipeBook(BaseModel):
    """All recipes for one bakery, plus the pantry they are costed against."""

    pantry: Pantry
    recipes: dict[str, Recipe] = Field(default_factory=dict)

    def add(self, *recipes: Recipe) -> RecipeBook:
        for recipe in recipes:
            self.recipes[recipe.item_id] = recipe
        return self

    def breakdown(self, item: MenuItem) -> CostBreakdown:
        try:
            recipe = self.recipes[item.id]
        except KeyError:
            raise KeyError(f"no recipe for {item.id!r}") from None
        return recipe.breakdown(item, self.pantry)

    def unit_cost(self, item: MenuItem) -> float:
        return self.breakdown(item).total

    def margin(self, item: MenuItem) -> float:
        return self.breakdown(item).margin(item)
