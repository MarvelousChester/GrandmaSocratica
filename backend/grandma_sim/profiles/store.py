"""SQLite storage for day-scheduled settings, in the same file as the menus.

A value set on day N stays in force for every later day until another day
sets its own, so a change carries forward without being re-sent daily. Menu
profiles and ingredient prices each get their own schedule.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from ..menu.store import connect
from .ingredients import IngredientPrices
from .overrides import DayProfile

T = TypeVar("T", bound=BaseModel)


class ScheduledProfile(BaseModel):
    """The profile in force on `day`, and the day it was set on."""

    day: int
    source_day: int | None = Field(
        description="Day the profile was set on; None means no profile, base menus."
    )
    profile: DayProfile


class ScheduledIngredientPrices(BaseModel):
    """The ingredient prices in force on `day`, and the day they were set on."""

    day: int
    source_day: int | None = Field(
        description="Day the prices were set on; None means base pantry prices."
    )
    prices: IngredientPrices


class ScheduleStore(Generic[T]):
    """Day-keyed values of one model type, one row per day they were set on.

    Opens a connection per call, so it is safe to share across the API's
    worker threads.
    """

    def __init__(self, path: str | Path, table: str, column: str, model: type[T]):
        """
        Open (creating if needed) a schedule table.

        Args:
         path: SQLite file.
         table: Table holding this schedule.
         column: Column holding each day's value as JSON.
         model: Pydantic model the values are stored as.
        """
        if not (table.isidentifier() and column.isidentifier()):
            raise ValueError("table and column must be plain identifiers")
        self.path = Path(path)
        self.table = table
        self.column = column
        self.model = model
        with self._connect() as conn:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {table} (
                        day      INTEGER PRIMARY KEY CHECK (day >= 0),
                        {column} TEXT NOT NULL
                    )"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits on success and always closes."""
        with closing(connect(self.path)) as conn, conn:
            yield conn

    def set(self, day: int, value: T) -> None:
        with self._connect() as conn:
            conn.execute(
                f"""INSERT INTO {self.table} (day, {self.column}) VALUES (?, ?)
                    ON CONFLICT(day) DO UPDATE SET {self.column}=excluded.{self.column}""",
                (day, value.model_dump_json()),
            )

    def delete(self, day: int) -> bool:
        """Remove the value set on `day`. False if there wasn't one."""
        with self._connect() as conn:
            cursor = conn.execute(f"DELETE FROM {self.table} WHERE day = ?", (day,))
            return cursor.rowcount > 0

    def latest(self, day: int) -> tuple[int, T] | None:
        """The value set most recently on or before `day`, with the day it was set."""
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT day, {self.column} FROM {self.table} WHERE day <= ? "
                "ORDER BY day DESC LIMIT 1",
                (day,),
            ).fetchone()
        if row is None:
            return None
        return row["day"], self.model.model_validate_json(row[self.column])

    def all(self) -> dict[int, T]:
        """Every value explicitly set, by the day it was set on, in day order."""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT day, {self.column} FROM {self.table} ORDER BY day"
            ).fetchall()
        return {
            row["day"]: self.model.model_validate_json(row[self.column]) for row in rows
        }
