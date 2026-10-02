"""Day profiles: per-item changes layered over the base menus for a day.

The base menus stay untouched in the menu store; a profile only says what is
different on a given day (a price cut, a sweeter recipe, an item pulled).
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field

from ..core.enums import Allergen, Daypart, FlavorCategory
from ..menu.items import Menu, MenuItem


class FlavorOverride(BaseModel):
    """Replacement values for an item's flavour. Unset fields keep the base."""

    sweet_savoury: float | None = None
    bitterness: float | None = None
    fruitiness: float | None = None
    categories: set[FlavorCategory] | None = None


class ItemOverride(BaseModel):
    """Changes to one menu item. Unset (or null) fields keep the base value."""

    available: bool = Field(True, description="False takes the item off the menu.")
    price: float | None = None
    portion_size_g: float | None = None
    flavor: FlavorOverride | None = None
    allergens: set[Allergen] | None = None
    daypart_weights: dict[Daypart, float] | None = None

    def apply(self, item: MenuItem) -> MenuItem:
        """
        Return a copy of `item` with this override's values swapped in.

        Args:
         item: The base menu item.

        Returns:
         A new, validated item.

        Raises:
         pydantic.ValidationError: If the result breaks a MenuItem constraint,
          e.g. a negative price or sweetness outside -1..1.
        """
        data = item.model_dump()
        data.update(self.model_dump(exclude_none=True, exclude={"available", "flavor"}))
        if self.flavor is not None:
            data["flavor"].update(self.flavor.model_dump(exclude_none=True))
        return MenuItem.model_validate(data)


class DayProfile(BaseModel):
    """Everything that differs from the base menus on a day, by item id."""

    items: dict[str, ItemOverride] = Field(default_factory=dict)

    def apply(self, menus: Sequence[Menu]) -> list[Menu]:
        """
        Build the menus as they stand on a day with this profile.

        Args:
         menus: The base menus.

        Returns:
         New menus with overrides applied and unavailable items removed.

        Raises:
         ValueError: If an override names an item that isn't on any menu, or
          produces an invalid item.
        """
        known = {item.id for menu in menus for item in menu.items}
        unknown = sorted(set(self.items) - known)
        if unknown:
            raise ValueError(f"no menu item with id(s): {', '.join(unknown)}")

        result = []
        for menu in menus:
            items = []
            for item in menu.items:
                override = self.items.get(item.id)
                if override is None:
                    items.append(item)
                elif override.available:
                    items.append(override.apply(item))
            result.append(Menu(bakery=menu.bakery, items=items))
        return result
