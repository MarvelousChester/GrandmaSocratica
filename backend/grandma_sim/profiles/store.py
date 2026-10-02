"""SQLite storage for day profiles, in the same database file as the menus.

A profile set on day N stays in force for every later day until another day
sets its own, so a price change carries forward without being re-sent daily.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from pydantic import BaseModel, Field

from ..menu.store import connect
from .overrides import DayProfile

SCHEMA = """
CREATE TABLE IF NOT EXISTS day_profiles (
    day     INTEGER PRIMARY KEY CHECK (day >= 1),
    profile TEXT NOT NULL  -- DayProfile as JSON
);
"""


class ScheduledProfile(BaseModel):
    """The profile in force on `day`, and the day it was set on."""

    day: int
    source_day: int | None = Field(
        description="Day the profile was set on; None means no profile, base menus."
    )
    profile: DayProfile


class ProfileStore:
    """Reads and writes day profiles. Opens a connection per call, so it is
    safe to share across the API's worker threads."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits on success and always closes."""
        with closing(connect(self.path)) as conn, conn:
            yield conn

    def set(self, day: int, profile: DayProfile) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO day_profiles (day, profile) VALUES (?, ?)
                   ON CONFLICT(day) DO UPDATE SET profile=excluded.profile""",
                (day, profile.model_dump_json()),
            )

    def delete(self, day: int) -> bool:
        """Remove the profile set on `day`. False if there wasn't one."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM day_profiles WHERE day = ?", (day,))
            return cursor.rowcount > 0

    def effective(self, day: int) -> ScheduledProfile:
        """The latest profile set on or before `day`, or an empty one."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT day, profile FROM day_profiles WHERE day <= ? "
                "ORDER BY day DESC LIMIT 1",
                (day,),
            ).fetchone()
        if row is None:
            return ScheduledProfile(day=day, source_day=None, profile=DayProfile())
        return _to_scheduled(day, row)

    def all(self) -> list[ScheduledProfile]:
        """Every explicitly set profile, in day order."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT day, profile FROM day_profiles ORDER BY day"
            ).fetchall()
        return [_to_scheduled(row["day"], row) for row in rows]


def _to_scheduled(day: int, row: sqlite3.Row) -> ScheduledProfile:
    return ScheduledProfile(
        day=day,
        source_day=row["day"],
        profile=DayProfile.model_validate_json(row["profile"]),
    )
