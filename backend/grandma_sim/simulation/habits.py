"""Habits: the pull a bakery earns by being where a customer keeps buying.

Kept apart from `CustomerProfile`, whose traits are fixed: habits change from
day to day. Every habit fades a little each day and buying at a bakery
strengthens the habit for it, so a customer won over by a price cut keeps
coming back for a while after the cut ends -- and drifts off if neglected.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pydantic import BaseModel, Field

from ..core.enums import Bakery
from .events import VisitEvent

# Habits weaker than this are dropped, so long runs don't accumulate dust.
_MIN_HABIT = 1e-3

Habits = dict[str, dict[Bakery, float]]


class HabitConfig(BaseModel):
    """How fast habits form and fade.

    A customer who buys at the same bakery every day levels off at
    `gain / (1 - retention)`; one who does so on a fraction p of days, at p
    times that.
    """

    retention: float = Field(
        0.9, ge=0.0, le=1.0, description="Share of a habit kept from one day to the next."
    )
    gain: float = Field(0.1, ge=0.0, description="Habit added by one purchase.")

    def update(
        self, habits: Mapping[str, Mapping[Bakery, float]], events: Iterable[VisitEvent]
    ) -> Habits:
        """
        Carry habits through one day: fade them all, then credit purchases.

        Args:
         habits: Each customer's habit per bakery going into the day.
         events: The day's visits.

        Returns:
         Habits going into the next day.
        """
        result: Habits = {
            customer_id: {bakery: self.retention * h for bakery, h in by_bakery.items()}
            for customer_id, by_bakery in habits.items()
        }
        for event in events:
            bakery = event.choice.bakery
            if bakery is not None:
                by_bakery = result.setdefault(event.customer_id, {})
                by_bakery[bakery] = by_bakery.get(bakery, 0.0) + self.gain

        # Drop faded habits, keeping customers and bakeries in a stable order.
        pruned: Habits = {}
        for customer_id in sorted(result):
            kept = {
                bakery: h
                for bakery, h in sorted(result[customer_id].items())
                if h >= _MIN_HABIT
            }
            if kept:
                pruned[customer_id] = kept
        return pruned


def mean_habit(
    habits: Mapping[str, Mapping[Bakery, float]], population: int
) -> dict[Bakery, float]:
    """Average habit per bakery across the whole town, habit-less customers included."""
    totals = {bakery: 0.0 for bakery in Bakery}
    for by_bakery in habits.values():
        for bakery, habit in by_bakery.items():
            totals[bakery] += habit
    return {
        bakery: total / population if population else 0.0
        for bakery, total in totals.items()
    }
