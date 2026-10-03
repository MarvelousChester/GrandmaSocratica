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
from grandma_sim.competition.pricing import Reason
from grandma_sim.menu.recipes_seed import recipe_books_by_bakery
from grandma_sim.menu.seed import build_menus
from grandma_sim.profiles.ingredients import IngredientPrices
from grandma_sim.profiles.overrides import DayProfile, FlavorOverride, ItemOverride
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


def parse_spike(text: str) -> tuple[int, str, float]:
    """'cream=12@5' -> (day 5, cream, 12x the usual price)."""
    try:
        ingredient_mult, _, day = text.partition("@")
        ingredient, _, multiplier = ingredient_mult.partition("=")
        return int(day or 0), ingredient, float(multiplier)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected ingredient=multiplier@day, got {text!r}"
        ) from None


def build_ingredient_prices(
    spikes: list[tuple[int, str, float]],
) -> dict[int, IngredientPrices]:
    """Turn scheduled spikes into per-day prices, each carrying the ones before."""
    standing: dict[str, float] = {}
    schedule: dict[int, IngredientPrices] = {}
    for day, ingredient, multiplier in sorted(spikes):
        standing[ingredient] = multiplier
        schedule[day] = IngredientPrices(multipliers=dict(standing))
    return schedule


def build_profiles(
    cuts: list[tuple[int, str, float]], sweetens: list[tuple[int, str, float]]
) -> dict[int, DayProfile]:
    """Turn grandma's scheduled changes into one profile per day she acts.

    A profile replaces the one before it rather than merging, so each day's
    profile has to carry every change made so far -- otherwise a cut on day 14
    would silently undo one made on day 2. The same goes across kinds: a
    reformulation must not drop an earlier price cut on the same item.
    """
    standing: dict[str, dict[str, float]] = {}
    profiles: dict[int, DayProfile] = {}
    changes = [(d, i, "price", v) for d, i, v in cuts]
    changes += [(d, i, "sweet", v) for d, i, v in sweetens]

    for day, item_id, field, value in sorted(changes):
        standing.setdefault(item_id, {})[field] = value
        profiles[day] = DayProfile(
            items={
                other: ItemOverride(
                    price=fields.get("price"),
                    flavor=(
                        FlavorOverride(sweet_savoury=fields["sweet"])
                        if "sweet" in fields
                        else None
                    ),
                )
                for other, fields in standing.items()
            }
        )
    return profiles


def describe(override: ItemOverride) -> list[str]:
    """What this override actually changes, in words."""
    parts = []
    if override.price is not None:
        parts.append(f"${override.price:.2f}")
    if override.flavor is not None and override.flavor.sweet_savoury is not None:
        parts.append(f"sweetness {override.flavor.sweet_savoury:+.2f}")
    return parts


def print_moves(profiles: dict[int, DayProfile], names: dict[str, str]) -> None:
    """Grandma's changes, printed the day each one first takes effect.

    Profiles carry everything set so far, so only what is new on a day is
    worth printing.
    """
    if not profiles:
        print("  (none -- both menus hold their opening prices)")
        return
    seen: dict[str, list[str]] = {}
    for day in sorted(profiles):
        for item_id, override in profiles[day].items.items():
            described = describe(override)
            new = [part for part in described if part not in seen.get(item_id, [])]
            if new:
                print(f"  day {day:>2}  {names[item_id]:<26} -> {', '.join(new)}")
            seen[item_id] = described


def print_rivalries(result: SeasonResult) -> None:
    for rivalry in result.rivalries:
        print(
            f"  {rivalry.watcher_name:<18} tracks {rivalry.rival_name:<26}"
            f"taste gap {rivalry.distance:.2f}"
        )


def print_responses(result: SeasonResult) -> None:
    """Each price move with the evidence behind it.

    A cost-floor rise is explained by their own costs, not by grandma's menu
    board -- they didn't act on her price, they acted on their margin.
    """
    if not result.all_repricings():
        print("  (The Bakery never moved -- it held share everywhere.)")
        return
    for change in result.all_repricings():
        if change.reason is Reason.COST_FLOOR:
            why = (
                f"{change.item_name} now costs them ${change.unit_cost:.2f}; "
                f"below ${change.floor:.2f} they lose money"
            )
        else:
            why = (
                f"saw {change.rival_name} at ${change.observed_rival_price:.2f} "
                f"on day {change.observed_on_day}, "
                f"held {change.observed_share:.0%} of the pair"
            )
        print(
            f"  day {change.day:>2}  {change.item_name:<18}"
            f"${change.old_price:>5.2f} -> ${change.new_price:>5.2f}  "
            f"{change.reason.value:<11}{why}"
        )


def print_retargeting(result: SeasonResult) -> None:
    """Days where a reformulation moved what The Bakery is shadowing."""
    previous = {r.watcher_id: r for r in result.rivalries}
    names = {r.watcher_id: r.watcher_name for r in result.rivalries}
    changed = False

    for record in result.days:
        if record.rivalries is None:
            continue
        current = {r.watcher_id: r for r in record.rivalries}
        names.update({r.watcher_id: r.watcher_name for r in record.rivalries})

        for watcher_id in sorted(previous.keys() | current.keys()):
            before, after = previous.get(watcher_id), current.get(watcher_id)
            if (before and before.rival_id) == (after and after.rival_id):
                continue
            changed = True
            name = names[watcher_id]
            if after is None:
                print(
                    f"  day {record.day:>2}  {name} dropped {before.rival_name} "
                    f"-- nothing on her menu is close enough any more"
                )
            elif before is None:
                print(f"  day {record.day:>2}  {name} started tracking {after.rival_name}")
            else:
                print(
                    f"  day {record.day:>2}  {name} switched from {before.rival_name} "
                    f"to {after.rival_name}"
                )
        previous = current

    if not changed:
        print("  (nobody re-targeted -- the menus kept their shape.)")


def mean_series(runs: list[list[float]]) -> list[float]:
    """Average several runs' per-day series into one."""
    return [sum(day) / len(runs) for day in zip(*runs)]


def print_windows(
    reactive: list[SeasonResult], flat: list[SeasonResult], bakery: Bakery
) -> None:
    """Grandma's share and profit per review cycle, with and without the response.

    Averaged over every seed run. One season's difference between reacting and
    frozen is well inside day-to-day noise -- on a single seed the sign flips
    about one time in six -- so a one-seed figure isn't worth printing.
    """
    window = reactive[0].config.policy.review_every_days
    days = len(reactive[0].days)

    live_share = mean_series([r.share_series(bakery) for r in reactive])
    base_share = mean_series([r.share_series(bakery) for r in flat])
    live_profit = mean_series([r.profit_series(bakery) for r in reactive])
    base_profit = mean_series([r.profit_series(bakery) for r in flat])

    print(
        f"  {'days':<9}{'share':>8}{'if frozen':>11}"
        f"{'profit/day':>13}{'if frozen':>11}{'cost':>9}"
    )
    for start in range(0, days, window):
        stop = min(start + window, days)
        span = stop - start

        def mean(series: list[float]) -> float:
            return sum(series[start:stop]) / span

        print(
            f"  {f'{start}-{stop - 1}':<9}{mean(live_share):>8.1%}"
            f"{mean(base_share):>11.1%}{mean(live_profit):>13.2f}"
            f"{mean(base_profit):>11.2f}{mean(live_profit) - mean(base_profit):>+9.2f}"
        )

    # Negative when responding hurt them -- a cost-driven rise hands her share.
    lost = sum(base_profit) - sum(live_profit)
    verb = "cost" if lost >= 0 else "gained"
    seeds = len(reactive)
    print(
        f"\n  Over {days} days The Bakery's response {verb} grandma "
        f"${abs(lost):,.2f} in gross profit"
        f"{f', averaged over {seeds} seeds' if seeds > 1 else ''}."
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
    parser.add_argument(
        "--sweeten",
        type=parse_cut,
        action="append",
        default=[],
        metavar="ITEM=SWEETNESS@DAY",
        help="reformulate an item, -1 savoury to +1 sweet, e.g. fall_parfait=-0.85@3",
    )
    parser.add_argument(
        "--spike",
        type=parse_spike,
        action="append",
        default=[],
        metavar="INGREDIENT=MULT@DAY",
        help="a market-wide ingredient price move, e.g. cream=3@5",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="how many seeds to average the share and profit over (default 5)",
    )
    parser.add_argument("--json", type=Path, help="also write the full SeasonResult")
    args = parser.parse_args()

    menus = list(build_menus())
    names = {i.id: i.name for menu in menus for i in menu.items}
    books = recipe_books_by_bakery()

    def season(seed: int, reactive: bool) -> SeasonResult:
        config = SeasonConfig(
            days=args.days,
            seed=seed,
            reactive=reactive,
            population=default_population(args.customers),
            profiles=build_profiles(args.cut, args.sweeten),
            ingredient_prices=build_ingredient_prices(args.spike),
        )
        return SeasonSimulator(config, menus, books).run()

    seeds = range(args.seed, args.seed + max(args.seeds, 1))
    reactive_runs = [season(seed, True) for seed in seeds]
    flat_runs = [season(seed, False) for seed in seeds]
    # The narrative sections describe one season; the figures average them all.
    reactive, config = reactive_runs[0], reactive_runs[0].config

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(reactive.model_dump_json(indent=2))
        print(f"wrote {args.json}\n")

    print(
        f"=== {args.days} days, {args.customers} customers, "
        f"seeds {seeds.start}-{seeds.stop - 1} ===\n"
        f"(moves and responses are from seed {args.seed}; "
        f"share and profit average every seed)"
    )
    sections = [
        ("Grandma's moves", lambda: print_moves(config.profiles, names)),
        ("Who watches whom", lambda: print_rivalries(reactive)),
        ("The Bakery's responses", lambda: print_responses(reactive)),
        ("Re-targeting", lambda: print_retargeting(reactive)),
        (
            "Grandma's share and profit",
            lambda: print_windows(reactive_runs, flat_runs, Bakery.GRANDMAS),
        ),
        ("Closing prices", lambda: print_prices(reactive, names)),
    ]
    for title, show in sections:
        print(f"\n--- {title} ---")
        show()


if __name__ == "__main__":
    main()
