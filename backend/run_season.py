"""Run a season and show how The Bakery answers grandma's price moves.

    uv run python run_season.py --cut fall_parfait=6.50@2
    uv run python run_season.py --days 42 --cut fall_parfait=6.50@2 --cut lemon_tart=4.95@14

Every run also simulates the same season with The Bakery's prices frozen, so
the columns show what grandma would have kept against what the response took
back.
"""

import argparse
from pathlib import Path

from grandma_sim import Bakery
from grandma_sim.customers.presets import default_population
from grandma_sim.menu.items import Menu
from grandma_sim.menu.recipes_seed import build_recipe_books
from grandma_sim.menu.seed import build_menus
from grandma_sim.profiles.overrides import DayProfile, ItemOverride
from grandma_sim.simulation.season import SeasonConfig, SeasonResult, SeasonSimulator


def parse_cut(text: str) -> tuple[int, str, float]:
    """'fall_parfait=6.50@2' -> (day 2, fall_parfait, $6.50)."""
    try:
        item_price, _, day = text.partition("@")
        item_id, _, price = item_price.partition("=")
        return int(day or 0), item_id, float(price)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected item_id=price@day, got {text!r}"
        ) from None


def build_profiles(cuts: list[tuple[int, str, float]]) -> dict[int, DayProfile]:
    """Turn scheduled cuts into profiles.

    A profile replaces the one before it rather than merging, so each day's
    profile has to carry every price set so far -- otherwise a cut on day 14
    would silently undo one made on day 2.
    """
    standing: dict[str, ItemOverride] = {}
    profiles: dict[int, DayProfile] = {}
    for day, item_id, price in sorted(cuts):
        standing[item_id] = ItemOverride(price=price)
        profiles[day] = DayProfile(items=dict(standing))
    return profiles


def unit_costs(menus: list[Menu]) -> dict[str, float]:
    """What each item costs its own bakery to make, at its base portion size."""
    costs: dict[str, float] = {}
    for menu, book in zip(menus, build_recipe_books()):
        for item in menu.items:
            costs[item.id] = book.breakdown(item).total
    return costs


def daily_profit(
    result: SeasonResult, bakery: Bakery, costs: dict[str, float], owned: set[str]
) -> list[float]:
    """Gross profit per day: units sold x (that day's price - unit cost)."""
    profits = []
    for record in result.days:
        profits.append(
            sum(
                units * (record.prices[item_id] - costs[item_id])
                for item_id, units in record.summary.item_sales.items()
                if item_id in owned
            )
        )
    return profits


def print_moves(profiles: dict[int, DayProfile], names: dict[str, str]) -> None:
    if not profiles:
        print("  (none -- both menus hold their opening prices)")
        return
    seen: dict[str, float] = {}
    for day in sorted(profiles):
        for item_id, override in profiles[day].items.items():
            if seen.get(item_id) != override.price:
                print(f"  day {day:>2}  {names[item_id]:<26} -> ${override.price:.2f}")
                seen[item_id] = override.price


def print_rivalries(result: SeasonResult) -> None:
    for rivalry in result.rivalries:
        print(
            f"  {rivalry.watcher_name:<18} tracks {rivalry.rival_name:<26}"
            f"taste gap {rivalry.distance:.2f}"
        )


def print_responses(result: SeasonResult) -> None:
    if not result.all_repricings():
        print("  (The Bakery never moved -- it held share everywhere.)")
        return
    for change in result.all_repricings():
        print(
            f"  day {change.day:>2}  {change.item_name:<18}"
            f"${change.old_price:>5.2f} -> ${change.new_price:>5.2f}  "
            f"{change.reason.value:<10} saw {change.rival_name} at "
            f"${change.observed_rival_price:.2f} on day {change.observed_on_day}, "
            f"held {change.observed_share:.0%} of the pair"
        )


def print_windows(
    reactive: SeasonResult, flat: SeasonResult, costs: dict[str, float], owned: set[str]
) -> None:
    """Grandma's share and profit per review cycle, with and without the response."""
    window = reactive.config.policy.review_every_days
    live_share = reactive.share_series(Bakery.GRANDMAS)
    base_share = flat.share_series(Bakery.GRANDMAS)
    live_profit = daily_profit(reactive, Bakery.GRANDMAS, costs, owned)
    base_profit = daily_profit(flat, Bakery.GRANDMAS, costs, owned)

    print(
        f"  {'days':<9}{'share':>8}{'if frozen':>11}"
        f"{'profit/day':>13}{'if frozen':>11}{'cost':>9}"
    )
    for start in range(0, len(reactive.days), window):
        stop = min(start + window, len(reactive.days))
        span = stop - start

        def mean(series: list[float]) -> float:
            return sum(series[start:stop]) / span

        print(
            f"  {f'{start}-{stop - 1}':<9}{mean(live_share):>8.1%}"
            f"{mean(base_share):>11.1%}{mean(live_profit):>13.2f}"
            f"{mean(base_profit):>11.2f}{mean(live_profit) - mean(base_profit):>+9.2f}"
        )

    lost = sum(base_profit) - sum(live_profit)
    print(
        f"\n  Over {len(reactive.days)} days the response cost grandma "
        f"${lost:,.2f} in gross profit."
    )


def print_prices(result: SeasonResult, names: dict[str, str]) -> None:
    opening, closing = result.days[0].prices, result.days[-1].prices
    moved = [i for i in closing if abs(closing[i] - opening.get(i, closing[i])) >= 0.01]
    if not moved:
        print("  (no prices changed)")
        return
    for item_id in moved:
        print(
            f"  {names[item_id]:<26} ${opening[item_id]:>5.2f} -> ${closing[item_id]:>5.2f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--customers", type=int, default=400)
    parser.add_argument(
        "--cut",
        type=parse_cut,
        action="append",
        default=[],
        metavar="ITEM=PRICE@DAY",
        help="a price grandma sets, e.g. fall_parfait=6.50@2",
    )
    parser.add_argument("--json", type=Path, help="also write the full SeasonResult")
    args = parser.parse_args()

    menus = list(build_menus())
    names = {i.id: i.name for menu in menus for i in menu.items}
    costs = unit_costs(menus)
    grandmas_items = {
        i.id for m in menus if m.bakery is Bakery.GRANDMAS for i in m.items
    }

    config = SeasonConfig(
        days=args.days,
        seed=args.seed,
        population=default_population(args.customers),
        profiles=build_profiles(args.cut),
    )
    reactive = SeasonSimulator(config, menus).run()
    flat = SeasonSimulator(config.model_copy(update={"reactive": False}), menus).run()

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(reactive.model_dump_json(indent=2))
        print(f"wrote {args.json}\n")

    print(f"=== {args.days} days, seed {args.seed}, {args.customers} customers ===")
    sections = [
        ("Grandma's moves", lambda: print_moves(config.profiles, names)),
        ("Who watches whom", lambda: print_rivalries(reactive)),
        ("The Bakery's responses", lambda: print_responses(reactive)),
        (
            "Grandma's share and profit",
            lambda: print_windows(reactive, flat, costs, grandmas_items),
        ),
        ("Closing prices", lambda: print_prices(reactive, names)),
    ]
    for title, show in sections:
        print(f"\n--- {title} ---")
        show()


if __name__ == "__main__":
    main()
