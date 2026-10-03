"""The money side of a day: revenue, ingredient cost and profit per bakery.

Built from the day's purchases and each bakery's recipe book. Costs use the
menus as they stood that day, so a bigger portion uses more ingredients. Every
figure is given for the whole day and for each opening hour.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field, computed_field

from ..core.clock import DayClock
from ..core.enums import Bakery
from ..menu.costing import CostBreakdown, Pantry, RecipeBook
from ..menu.items import Menu
from .events import VisitEvent


class IngredientUsage(BaseModel):
    name: str
    price_per_kg: float = Field(description="What the bakery paid that day.")
    grams: float = 0.0
    cost: float = 0.0


class Financials(BaseModel):
    units_sold: int = 0
    revenue: float = 0.0
    ingredient_cost: float = 0.0

    @computed_field
    @property
    def profit(self) -> float:
        return round(self.revenue - self.ingredient_cost, 2)


class LedgerPeriod(BaseModel):
    """Sales, costs and ingredients used over some span of the day."""

    financials: Financials = Field(default_factory=Financials)
    ingredients: dict[str, IngredientUsage] = Field(
        default_factory=dict, description="By ingredient id, costliest first."
    )

    def record(self, price: float, cost: CostBreakdown | None, pantry: Pantry | None) -> None:
        """Add one sale. `cost` is None for items without a recipe."""
        self.financials.units_sold += 1
        self.financials.revenue += price
        if cost is None:
            return
        self.financials.ingredient_cost += cost.total
        for line in cost.lines:
            usage = self.ingredients.get(line.ingredient_id)
            if usage is None:
                ingredient = pantry.ingredients[line.ingredient_id]
                usage = self.ingredients[line.ingredient_id] = IngredientUsage(
                    name=ingredient.name, price_per_kg=round(ingredient.price_per_kg, 2)
                )
            usage.grams += line.grams
            usage.cost += line.cost

    def finalise(self) -> None:
        """Round for display and order ingredients by cost."""
        self.financials.revenue = round(self.financials.revenue, 2)
        self.financials.ingredient_cost = round(self.financials.ingredient_cost, 2)
        for usage in self.ingredients.values():
            usage.grams = round(usage.grams, 1)
            usage.cost = round(usage.cost, 2)
        self.ingredients = dict(
            sorted(self.ingredients.items(), key=lambda kv: kv[1].cost, reverse=True)
        )


class HourLedger(LedgerPeriod):
    hour: int = Field(description="Hour of day the period starts, e.g. 7 = 07:00-08:00.")


class BakeryLedger(LedgerPeriod):
    """A bakery's whole day, plus the same breakdown for every opening hour."""

    hourly: list[HourLedger] = Field(default_factory=list)


class DayLedger(BaseModel):
    bakeries: dict[Bakery, BakeryLedger]
    uncosted_items: list[str] = Field(
        default_factory=list,
        description="Menu items with no recipe; their sales count as revenue at 0 cost.",
    )

    @classmethod
    def build(
        cls,
        events: Sequence[VisitEvent],
        menus: Sequence[Menu],
        recipe_books: Mapping[Bakery, RecipeBook],
        clock: DayClock,
    ) -> DayLedger:
        """
        Total up the day's purchases into a ledger per bakery.

        Args:
         events: The day's visits, in time order.
         menus: The menus as they stood that day.
         recipe_books: Each bakery's recipes and ingredient prices.
         clock: Opening hours, which set the hourly buckets.

        Returns:
         The ledger, with an entry for every opening hour (empty hours too).
        """
        costs: dict[str, CostBreakdown] = {}
        uncosted: list[str] = []
        for menu in menus:
            book = recipe_books.get(menu.bakery)
            for item in menu.items:
                if book is not None and item.id in book.recipes:
                    costs[item.id] = book.breakdown(item)
                else:
                    uncosted.append(item.id)

        hours = range(clock.open_minute // 60, math.ceil(clock.close_minute / 60))
        ledgers = {
            bakery: BakeryLedger(hourly=[HourLedger(hour=h) for h in hours])
            for bakery in Bakery
        }

        # Record each purchase against its bakery's day and hour.
        for event in events:
            choice = event.choice
            if not choice.purchased:
                continue
            ledger = ledgers[choice.bakery]
            hour = ledger.hourly[int(event.minute // 60) - hours.start]
            book = recipe_books.get(choice.bakery)
            pantry = book.pantry if book is not None else None
            cost = costs.get(choice.item_id)
            ledger.record(choice.price, cost, pantry)
            hour.record(choice.price, cost, pantry)

        for ledger in ledgers.values():
            ledger.finalise()
            for hour in ledger.hourly:
                hour.finalise()
        return cls(bakeries=ledgers, uncosted_items=sorted(uncosted))
