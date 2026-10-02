"""Which item competes with which.

Pairs are found by taste rather than declared by hand: for each of the
watcher's items, the closest item on the rival menu, if it's close enough to
count as the same thing. That reuses the flavour meters the whole sim already
runs on, so a new item starts competing the moment someone adds it -- nobody
has to remember to update a lookup table.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..menu.items import Menu, MenuItem

# How much a category mismatch counts against an otherwise close pair. The
# meters alone can't tell a lemon square from a pumpkin parfait -- both land
# around 'sweet and fruity' -- so the flavour tags break those ties.
CATEGORY_PENALTY = 0.15


class Rivalry(BaseModel):
    """One item shadowing another on the opposite menu."""

    watcher_id: str = Field(description="The item that reacts.")
    watcher_name: str
    rival_id: str = Field(description="The item on the other menu it tracks.")
    rival_name: str
    distance: float = Field(description="Taste distance, 0..1. Lower = closer copy.")


def match_score(item: MenuItem, other: MenuItem) -> float:
    """Taste distance, worsened when the two don't share flavour tags.

    An untagged pair is judged on meters alone rather than penalised, so two
    plain loaves still match each other.
    """
    distance = item.tastes_like(other)
    if not item.flavor.categories and not other.flavor.categories:
        return distance
    overlap = item.flavor.category_overlap(other.flavor)
    return distance + CATEGORY_PENALTY * (1.0 - overlap)


def find_rivalries(
    watcher: Menu, rival: Menu, max_distance: float = 0.25
) -> list[Rivalry]:
    """
    Pair up every watcher item with its nearest rival by taste.

    Items with no rival inside `max_distance` are left out -- grandma's
    sourdough and The Bakery's turkey club aren't competing for the same
    customer, so neither should react to the other's price.

    Args:
     watcher: The menu that will react (The Bakery).
     rival: The menu being watched (grandma's).
     max_distance: Match score beyond which two items aren't substitutes.

    Returns:
     One rivalry per matched watcher item, closest pairs first.
    """
    pairs: list[Rivalry] = []
    for item in watcher.items:
        nearest = rival.closest_to(item, score=match_score)
        if nearest is None or match_score(item, nearest) > max_distance:
            continue
        pairs.append(
            Rivalry(
                watcher_id=item.id,
                watcher_name=item.name,
                rival_id=nearest.id,
                rival_name=nearest.name,
                distance=item.tastes_like(nearest),
            )
        )
    return sorted(pairs, key=lambda r: r.distance)
