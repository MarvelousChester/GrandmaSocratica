"""Menu items: one record per thing a bakery sells."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field, field_serializer

from ..core.enums import Allergen, Bakery, Daypart, ItemCategory
from ..core.flavor import FlavorProfile


class MenuItem(BaseModel):
    """One thing on a menu, with everything the customer sim scores it on."""

    id: str
    name: str
    bakery: Bakery
    category: ItemCategory = ItemCategory.PASTRY
    description: str = ""

    flavor: FlavorProfile = Field(default_factory=FlavorProfile)
    price: float = Field(ge=0.0)
    portion_size_g: float = Field(gt=0.0)
    allergens: set[Allergen] = Field(default_factory=set)

    daypart_weights: dict[Daypart, float] = Field(
        default_factory=dict,
        description=(
            "'Occasion' as time of day: how strongly this item pulls at each "
            "daypart, 0..1. Anything unlisted defaults to 0.5 -- the parfait "
            "sells in the afternoon, not at 7am."
        ),
    )

    @field_serializer("allergens")
    def _sorted_allergens(self, allergens: set[Allergen]) -> list[str]:
        """Sets have no stable order across runs; sort so output is reproducible."""
        return sorted(a.value for a in allergens)

    def appeal_at(self, daypart: Daypart) -> float:
        return self.daypart_weights.get(daypart, 0.5)

    def best_daypart(self) -> Daypart | None:
        """When this item sells hardest."""
        if not self.daypart_weights:
            return None
        return max(self.daypart_weights, key=self.daypart_weights.get)

    def safe_for(self, avoided: set[Allergen]) -> bool:
        """False if the item trips any allergen the customer avoids."""
        return not (self.allergens & avoided)

    def tastes_like(self, other: MenuItem) -> float:
        """0.0 = identical, 1.0 = opposite. Shorthand for comparing two items."""
        return self.flavor.distance(other.flavor)


class Menu(BaseModel):
    """Everything one bakery sells."""

    bakery: Bakery
    items: list[MenuItem] = Field(default_factory=list)

    def add(self, *items: MenuItem) -> Menu:
        self.items.extend(items)
        return self

    def get(self, item_id: str) -> MenuItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(f"no item {item_id!r} on the {self.bakery.value} menu")

    def served_at(self, daypart: Daypart, threshold: float = 0.3) -> list[MenuItem]:
        """Items worth offering at this time of day, strongest pull first."""
        matches = [i for i in self.items if i.appeal_at(daypart) >= threshold]
        return sorted(matches, key=lambda i: i.appeal_at(daypart), reverse=True)

    def safe_for(self, avoided: set[Allergen]) -> list[MenuItem]:
        return [item for item in self.items if item.safe_for(avoided)]

    def closest_to(
        self, target: MenuItem, score: Callable[[MenuItem, MenuItem], float] | None = None
    ) -> MenuItem | None:
        """The item here that tastes most like `target`.

        Point it at grandma's Fall Parfait and it finds The Bakery's Autumn
        Parfait -- the knock-off, found by taste rather than by name.

        Args:
         target: The item to match against.
         score: How to measure the gap, lower being closer. Defaults to raw
          taste distance; pass one that also weighs flavour categories when
          the meters alone can't separate two items.

        Returns:
         The nearest item, or None if this menu is empty.
        """
        measure = score or (lambda a, b: a.tastes_like(b))
        return min(self.items, key=lambda item: measure(target, item), default=None)
