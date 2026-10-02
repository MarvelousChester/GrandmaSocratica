"""SQLite storage for both bakeries' menus.

Plain stdlib `sqlite3`, one file on disk, no server. One row per menu item:
the flavour meters are real columns so the customer-matching side can score
items straight from SQL, and the set-valued fields (allergens, categories,
daypart weights) are JSON.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..core.enums import Allergen, Bakery, Daypart, FlavorCategory
from ..core.flavor import FlavorProfile
from .items import Menu, MenuItem

DEFAULT_DB_PATH = Path("grandma.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_items (
    id              TEXT PRIMARY KEY,
    bakery          TEXT NOT NULL,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',

    price           REAL NOT NULL CHECK (price >= 0),
    portion_size_g  REAL NOT NULL CHECK (portion_size_g > 0),

    -- flavour meters: sweet_savoury is -1 (savoury) .. +1 (sweet),
    -- the other two are 0..1
    sweet_savoury   REAL NOT NULL CHECK (sweet_savoury BETWEEN -1 AND 1),
    bitterness      REAL NOT NULL CHECK (bitterness BETWEEN 0 AND 1),
    fruitiness      REAL NOT NULL CHECK (fruitiness BETWEEN 0 AND 1),

    categories      TEXT NOT NULL DEFAULT '[]',  -- JSON array: choc, vanilla, ...
    allergens       TEXT NOT NULL DEFAULT '[]',  -- JSON array
    daypart_weights TEXT NOT NULL DEFAULT '{}'   -- JSON {daypart: 0..1}
);

CREATE INDEX IF NOT EXISTS idx_menu_items_bakery ON menu_items(bakery);
"""


def connect(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _json_list(values) -> str:
    """Sets serialise unordered, which makes diffs noisy. Sort them."""
    return json.dumps(sorted(v.value if hasattr(v, "value") else v for v in values))


# ---- writes -----------------------------------------------------------


def save_item(conn: sqlite3.Connection, item: MenuItem) -> None:
    conn.execute(
        """INSERT INTO menu_items
               (id, bakery, name, category, description, price, portion_size_g,
                sweet_savoury, bitterness, fruitiness,
                categories, allergens, daypart_weights)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
               bakery=excluded.bakery, name=excluded.name,
               category=excluded.category, description=excluded.description,
               price=excluded.price, portion_size_g=excluded.portion_size_g,
               sweet_savoury=excluded.sweet_savoury,
               bitterness=excluded.bitterness, fruitiness=excluded.fruitiness,
               categories=excluded.categories, allergens=excluded.allergens,
               daypart_weights=excluded.daypart_weights""",
        (
            item.id,
            item.bakery.value,
            item.name,
            item.category.value,
            item.description,
            item.price,
            item.portion_size_g,
            item.flavor.sweet_savoury,
            item.flavor.bitterness,
            item.flavor.fruitiness,
            _json_list(item.flavor.categories),
            _json_list(item.allergens),
            json.dumps({d.value: w for d, w in item.daypart_weights.items()}),
        ),
    )


def save_menu(conn: sqlite3.Connection, menu: Menu) -> None:
    for item in menu.items:
        save_item(conn, item)
    conn.commit()


# ---- reads ------------------------------------------------------------


def _to_item(row: sqlite3.Row) -> MenuItem:
    return MenuItem(
        id=row["id"],
        bakery=Bakery(row["bakery"]),
        name=row["name"],
        category=row["category"],
        description=row["description"],
        price=row["price"],
        portion_size_g=row["portion_size_g"],
        flavor=FlavorProfile(
            sweet_savoury=row["sweet_savoury"],
            bitterness=row["bitterness"],
            fruitiness=row["fruitiness"],
            categories={FlavorCategory(c) for c in json.loads(row["categories"])},
        ),
        allergens={Allergen(a) for a in json.loads(row["allergens"])},
        daypart_weights={
            Daypart(k): v for k, v in json.loads(row["daypart_weights"]).items()
        },
    )


def load_menu(conn: sqlite3.Connection, bakery: Bakery) -> Menu:
    rows = conn.execute(
        "SELECT * FROM menu_items WHERE bakery = ? ORDER BY name", (bakery.value,)
    )
    return Menu(bakery=bakery).add(*(_to_item(row) for row in rows))


def menu_rows(conn: sqlite3.Connection, bakery: Bakery | None = None) -> list[dict]:
    """Flat dicts -- the handoff for the customer matcher.

    Same columns as the table, but with the JSON fields already parsed, so
    scoring a customer against a menu needs nothing from this package.
    """
    if bakery is None:
        rows = conn.execute("SELECT * FROM menu_items ORDER BY bakery, name")
    else:
        rows = conn.execute(
            "SELECT * FROM menu_items WHERE bakery = ? ORDER BY name", (bakery.value,)
        )

    out = []
    for row in rows:
        record = dict(row)
        for field in ("categories", "allergens", "daypart_weights"):
            record[field] = json.loads(record[field])
        out.append(record)
    return out


# ---- bootstrap --------------------------------------------------------


def build(path: str | Path = DEFAULT_DB_PATH, reset: bool = False) -> sqlite3.Connection:
    """Create the DB and fill it from `seed.py`."""
    from .seed import build_menus

    path = Path(path)
    if reset and path.exists():
        path.unlink()

    conn = connect(path)
    init_schema(conn)
    for menu in build_menus():
        save_menu(conn, menu)
    return conn


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    conn = build(target, reset=True)
    rows = menu_rows(conn)
    print(f"built {target} with {len(rows)} items")
    for row in rows:
        print(
            f"  {row['bakery']:<18} {row['name']:<24} ${row['price']:>5.2f}  "
            f"sweet {row['sweet_savoury']:>+.2f}  {row['portion_size_g']:.0f}g"
        )
