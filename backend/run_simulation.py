"""Run one simulated day against the seed menus and print a readable report.

    uv run python run_simulation.py --seed 3 --customers 600 --events 15
    uv run python run_simulation.py --json ../frontend/sample_data/day_seed0.json
"""

import argparse
from collections import Counter
from pathlib import Path

from grandma_sim import Bakery, DayConfig, DayResult, DaySimulator
from grandma_sim.customers.presets import default_population
from grandma_sim.menu.recipes_seed import recipe_books_by_bakery
from grandma_sim.menu.seed import build_menus

BAKERY_LABELS = {Bakery.GRANDMAS: "Grandma's", Bakery.THE_BAKERY: "The Bakery"}
WALKAWAY = "walked away"


def outcome_label(bakery: Bakery | None) -> str:
    return BAKERY_LABELS[bakery] if bakery else WALKAWAY


def print_totals(result: DayResult) -> None:
    summary = result.summary
    print(
        f"{len(result.customers)} customers, {summary.visits} visits, "
        f"{summary.purchases} purchases, {summary.walkaways} walked away\n"
    )
    for bakery, label in BAKERY_LABELS.items():
        totals = summary.by_bakery[bakery]
        print(
            f"  {label:<12} {totals.purchases:>4} sold  ${totals.revenue:>8.2f}  "
            f"{summary.market_share(bakery):>6.1%} share"
        )


def print_by_segment(result: DayResult) -> None:
    columns = [*BAKERY_LABELS.values(), WALKAWAY]
    counts = Counter(
        (e.segment, outcome_label(e.choice.bakery)) for e in result.events
    )
    segments = sorted({e.segment for e in result.events})

    print(f"\n  {'segment':<14}" + "".join(f"{c:>13}" for c in columns))
    for segment in segments:
        row = "".join(f"{counts[(segment, c)]:>13}" for c in columns)
        print(f"  {segment:<14}{row}")


def print_by_hour(result: DayResult) -> None:
    """One row per opening hour: a bar of visits, split by outcome."""
    hours: dict[int, Counter] = {}
    for event in result.events:
        hour = int(event.minute // 60)
        hours.setdefault(hour, Counter())[outcome_label(event.choice.bakery)] += 1

    print(f"\n  {'hour':<7}{'G':>4}{'B':>4}{'-':>4}")
    clock = result.config.clock
    for hour in range(clock.open_minute // 60, -(-clock.close_minute // 60)):
        tally = hours.get(hour, Counter())
        grandmas = tally[BAKERY_LABELS[Bakery.GRANDMAS]]
        the_bakery = tally[BAKERY_LABELS[Bakery.THE_BAKERY]]
        walked = tally[WALKAWAY]
        bar = "G" * grandmas + "B" * the_bakery + "-" * walked
        print(f"  {hour:02d}:00 {grandmas:>4}{the_bakery:>4}{walked:>4}  {bar}")
    print("  (G = Grandma's, B = The Bakery, - = walked away)")


def print_item_sales(result: DayResult, item_names: dict[str, tuple[str, Bakery]]) -> None:
    print()
    for item_id, count in result.summary.item_sales.items():
        name, bakery = item_names[item_id]
        print(f"  {name:<26} {BAKERY_LABELS[bakery]:<12} {count:>4}")


def print_ledger(result: DayResult, top_ingredients: int = 5) -> None:
    """Per bakery: day totals, costliest ingredients, then profit by hour."""
    for bakery, label in BAKERY_LABELS.items():
        ledger = result.ledger.bakeries[bakery]
        money = ledger.financials
        print(
            f"\n  {label}: revenue ${money.revenue:.2f}, ingredients "
            f"${money.ingredient_cost:.2f}, profit ${money.profit:.2f}"
        )
        for usage in list(ledger.ingredients.values())[:top_ingredients]:
            print(f"    {usage.name:<16} {usage.grams / 1000:>7.2f} kg  ${usage.cost:>7.2f}")

        hourly = "  ".join(
            f"{h.hour:02d}h ${h.financials.profit:.0f}"
            for h in ledger.hourly
            if h.financials.units_sold
        )
        print(f"    profit by hour: {hourly}")
    if result.ledger.uncosted_items:
        print(f"\n  no recipe (cost counted as 0): {', '.join(result.ledger.uncosted_items)}")


def print_sample_events(result: DayResult, limit: int) -> None:
    """The first `limit` visits, with the two terms that drove each purchase."""
    print()
    for event in result.events[:limit]:
        choice = event.choice
        line = f"  {event.time}  {event.customer_id}  {event.segment:<13}"
        if not choice.purchased:
            print(f"{line}{WALKAWAY:<38} p={choice.probability:.2f}")
            continue

        terms = choice.breakdown.model_dump()
        drivers = sorted(terms.items(), key=lambda kv: abs(kv[1]), reverse=True)[:2]
        why = ", ".join(f"{name} {value:+.2f}" for name, value in drivers)
        bought = f"{choice.item_name} ({BAKERY_LABELS[choice.bakery]})"
        print(f"{line}{bought:<38} p={choice.probability:.2f}  [{why}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--customers", type=int, default=400)
    parser.add_argument("--events", type=int, default=10, help="sample visits to show")
    parser.add_argument("--json", type=Path, help="also write the full DayResult here")
    args = parser.parse_args()

    menus = build_menus()
    config = DayConfig(seed=args.seed, population=default_population(args.customers))
    result = DaySimulator(config, menus, recipe_books_by_bakery()).run()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(result.model_dump_json(indent=2))
        print(f"wrote {args.json}")
    item_names = {i.id: (i.name, i.bakery) for menu in menus for i in menu.items}

    sections = [
        ("Totals", lambda: print_totals(result)),
        ("By segment", lambda: print_by_segment(result)),
        ("By hour", lambda: print_by_hour(result)),
        ("Item sales", lambda: print_item_sales(result, item_names)),
        ("Costs and profit", lambda: print_ledger(result)),
        (f"First {args.events} visits", lambda: print_sample_events(result, args.events)),
    ]
    print(f"=== Simulated day, seed {args.seed} ===")
    for title, show in sections:
        print(f"\n--- {title} ---")
        show()


if __name__ == "__main__":
    main()
