"""What a simulated day produces: a time-ordered log plus its totals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, Field

from ..choice.model import Choice
from ..core.enums import Bakery, Daypart


class VisitEvent(BaseModel):
    """One customer arriving and deciding. The frontend replays these in order."""

    minute: float
    time: str = Field(description="'HH:MM', for display.")
    daypart: Daypart
    customer_id: str
    segment: str
    choice: Choice


class BakeryTotals(BaseModel):
    purchases: int = 0
    revenue: float = 0.0


class DaySummary(BaseModel):
    visits: int
    walkaways: int
    by_bakery: dict[Bakery, BakeryTotals]
    item_sales: dict[str, int]

    @classmethod
    def from_events(cls, events: Sequence[VisitEvent]) -> DaySummary:
        by_bakery = {bakery: BakeryTotals() for bakery in Bakery}
        item_sales: Counter[str] = Counter()

        # Tally each purchase against its bakery and item.
        for event in events:
            choice = event.choice
            if not choice.purchased:
                continue
            totals = by_bakery[choice.bakery]
            totals.purchases += 1
            totals.revenue += choice.price
            item_sales[choice.item_id] += 1

        return cls(
            visits=len(events),
            walkaways=sum(1 for e in events if not e.choice.purchased),
            by_bakery=by_bakery,
            item_sales=dict(item_sales.most_common()),
        )

    @property
    def purchases(self) -> int:
        return sum(t.purchases for t in self.by_bakery.values())

    def market_share(self, bakery: Bakery) -> float:
        """Share of all purchases that went to `bakery`, 0..1."""
        if not self.purchases:
            return 0.0
        return self.by_bakery[bakery].purchases / self.purchases
