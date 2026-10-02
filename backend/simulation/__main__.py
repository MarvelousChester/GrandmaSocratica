"""Run one day against the seed menus and print the totals.

    uv run python -m backend.simulation [seed]
"""

import sys

from ..core.enums import Bakery
from ..menu.seed import build_menus
from .day import DayConfig, DaySimulator


def main(seed: int = 0) -> None:
    result = DaySimulator(DayConfig(seed=seed), build_menus()).run()
    summary = result.summary

    print(
        f"seed {seed}: {len(result.customers)} customers, {summary.visits} visits, "
        f"{summary.purchases} purchases, {summary.walkaways} walkaways"
    )
    for bakery in Bakery:
        totals = summary.by_bakery[bakery]
        print(
            f"  {bakery.value:<18} {totals.purchases:>4} sold  "
            f"${totals.revenue:>8.2f}  {summary.market_share(bakery):>5.1%} share"
        )
    print("  top items:")
    for item_id, count in list(summary.item_sales.items())[:5]:
        print(f"    {item_id:<20} {count:>4}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
