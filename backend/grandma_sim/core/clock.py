"""Time of day: opening hours and the minute <-> daypart mapping.

Time is minutes since midnight throughout the sim. Dayparts are buckets with
configurable start times; `daypart_mix()` blends neighbouring buckets so an
item's appeal ramps smoothly instead of jumping at 11:00 sharp.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .enums import Daypart


def _default_starts() -> dict[Daypart, int]:
    return {
        Daypart.EARLY_MORNING: 6 * 60,
        Daypart.MORNING: 8 * 60,
        Daypart.LUNCH: 11 * 60,
        Daypart.AFTERNOON: 14 * 60,
        Daypart.EVENING: 17 * 60,
    }


class DayClock(BaseModel):
    """Opening hours and where each daypart begins."""

    open_minute: int = Field(6 * 60, ge=0, lt=24 * 60)
    close_minute: int = Field(20 * 60, gt=0, le=24 * 60)
    daypart_starts: dict[Daypart, int] = Field(default_factory=_default_starts)

    @model_validator(mode="after")
    def _check(self) -> DayClock:
        if self.close_minute <= self.open_minute:
            raise ValueError("close_minute must be after open_minute")
        if set(self.daypart_starts) != set(Daypart):
            raise ValueError("daypart_starts must give a start for every Daypart")
        return self

    def _ordered(self) -> list[tuple[Daypart, int]]:
        return sorted(self.daypart_starts.items(), key=lambda kv: kv[1])

    def _midpoints(self) -> list[tuple[Daypart, float]]:
        """Centre of each daypart; the last one runs until closing."""
        ordered = self._ordered()
        ends = [start for _, start in ordered[1:]] + [self.close_minute]
        return [(dp, (start + end) / 2) for (dp, start), end in zip(ordered, ends)]

    def is_open(self, minute: float) -> bool:
        return self.open_minute <= minute < self.close_minute

    def daypart_at(self, minute: float) -> Daypart:
        """The bucket `minute` falls in (before the first start counts as first)."""
        ordered = self._ordered()
        current = ordered[0][0]
        for daypart, start in ordered:
            if minute >= start:
                current = daypart
        return current

    def daypart_mix(self, minute: float) -> dict[Daypart, float]:
        """
        Blend weights over dayparts at `minute`, summing to 1.

        Interpolates linearly between the midpoints of the two surrounding
        dayparts; before the first midpoint or after the last, it is entirely
        that daypart.

        Args:
         minute: Minutes since midnight.

        Returns:
         Mapping of daypart to weight, containing one or two entries.
        """
        midpoints = self._midpoints()
        if minute <= midpoints[0][1]:
            return {midpoints[0][0]: 1.0}

        # Walk adjacent pairs of midpoints to find the one bracketing `minute`.
        for (left, left_mid), (right, right_mid) in zip(midpoints, midpoints[1:]):
            if minute <= right_mid:
                t = (minute - left_mid) / (right_mid - left_mid)
                return {left: 1.0 - t, right: t}
        return {midpoints[-1][0]: 1.0}

    @staticmethod
    def format(minute: float) -> str:
        """Minutes since midnight as 'HH:MM'."""
        total = int(minute)
        return f"{total // 60:02d}:{total % 60:02d}"
