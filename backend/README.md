# Grandma's Bakeria — backend

The `grandma_sim` package: both bakeries' menus, the generated customer
population, the choice model, and the whole-day simulation.

## Run it

All commands run from `backend/`:

```bash
uv sync                                   # Python 3.11+, pydantic, numpy
uv run python -m grandma_sim.menu.store   # creates ./grandma.db, seeds 6 items per bakery
uv run python -m grandma_sim.simulation   # simulates one day, prints totals (optional seed arg)
uv run python run_simulation.py           # fuller report; --seed, --customers, --events
uv run python run_simulation.py --json ../frontend/sample_data/day_seed0.json
```

The DB is gitignored — rebuild any time, it's generated from
`grandma_sim/menu/seed.py`.

## The item model

| field | |
|---|---|
| **flavour meters** | `sweet_savoury` (−1 savoury … +1 sweet), `bitterness` (0…1), `fruitiness` (0…1) |
| **categories** | `chocolate`, `vanilla`, `caramel`, `fruit`, `berry`, `citrus`, `nut`, `coffee`, `spice`, `herbal`, `floral`, `cheese`, `savoury` |
| **price** | dollars |
| **portion size** | grams |
| **allergens** | `gluten`, `dairy`, `egg`, `tree_nut`, `peanut`, `soy`, `sesame` |
| **occasion** | `daypart_weights` — pull at each time of day, 0…1, over `early_morning`, `morning`, `lunch`, `afternoon`, `evening`. Anything unlisted defaults to 0.5. |

Plus `id`, `name`, `bakery`, `category` (pastry / cake / dessert / bread /
sandwich / drink) and `description`.

## Reading it from the customer-matching side

One table, `menu_items`. The three flavour meters are real float columns, so
scoring is doable in pure SQL:

```sql
SELECT id, bakery, name, price, portion_size_g,
       sweet_savoury, bitterness, fruitiness,
       categories, allergens, daypart_weights
FROM menu_items
WHERE bakery = 'grandmas_bakeria';
```

`categories`, `allergens` and `daypart_weights` are JSON columns. From Python,
`store.menu_rows(conn, bakery)` returns the same rows with those already
parsed into lists/dicts.

**Customer profiles should reuse `FlavorProfile` for their preference vector.**
Same shape on both sides means `customer_pref.distance(item.flavor)` gives a
0…1 taste-match score for free — 0 is a perfect match, 1 is as far apart as the
meters allow. `category_overlap()` is kept separate so the matching code can
weight "tastes similar" against "is tagged chocolate" however it wants.

Helpers on `Menu`, if useful:

```python
menu.served_at(Daypart.LUNCH)        # items that pull at that hour, strongest first
menu.safe_for({Allergen.DAIRY})      # items a dairy-avoidant customer can eat
menu.closest_to(fall_parfait)        # nearest item by taste
```

That last one, pointed at The Bakery's menu, finds the Autumn Parfait at a
distance of 0.05 — the knock-off, identified by taste rather than by name.

## Seed data

Six items per bakery. The contrast is deliberate: The Bakery is sweeter,
cheaper and smaller-portioned across the board, grandma's is savoury-capable,
pricier and more generous — so a customer's price sensitivity and their sweet
tooth pull in different directions rather than agreeing.

Add items in `grandma_sim/menu/seed.py` and re-run the build.

## Customer simulation

A day is fixed up front by a `DayConfig` (seed, population, clock, choice
parameters) and simulated in one go into a `DayResult`: the generated
customers, a time-ordered list of `VisitEvent`s for the frontend to replay,
and a `DaySummary`. Same config and menus always produce the same day.

- **Population** — `PopulationConfig` is a mixture of `SegmentConfig`s
  (commuter, lunch worker, student, regular in `customers/presets.py`). Each
  segment has a share and a distribution spec (`normal`, `beta`, `uniform`,
  `constant`) per trait, and the whole config round-trips through JSON.
- **Arrivals** — each customer visits with their own probability, at their
  preferred minute plus jitter. Arrivals outside opening hours don't happen.
- **Choice** — a multinomial logit over every allergen-safe item on both menus
  plus "buy nothing". Utility is a sum of taste match, flavour-category
  affinity, daypart appeal (blended between neighbouring dayparts), log price,
  log portion and bakery bias. Each purchase records its `UtilityBreakdown`.

## Layout

```
backend/
  pyproject.toml, uv.lock
  run_simulation.py    run a day and print a report, optionally write JSON
  grandma_sim/
    core/
      enums.py         allergens, dayparts, flavour categories, item categories, bakeries
      flavor.py        FlavorProfile — the meters, distance(), category_overlap()
      clock.py         DayClock — opening hours, minute -> daypart, daypart blending
    menu/
      items.py         MenuItem, Menu
      seed.py          both menus
      store.py         SQLite schema, read/write, menu_rows()
    customers/
      distributions.py Normal / Beta / Uniform / Constant specs
      profile.py       CustomerProfile — one generated customer
      population.py    SegmentConfig, PopulationConfig.generate()
      presets.py       default four-segment population
    choice/
      utility.py       UtilityWeights, UtilityModel.score() -> UtilityBreakdown
      model.py         ChoiceConfig, ChoiceModel (logit), Choice
    simulation/
      events.py        VisitEvent, DaySummary
      day.py           DayConfig, DaySimulator.run() -> DayResult
```

## Not done yet

- Baskets (one item per visit for now), inventory and queues.
- Multi-day state, e.g. loyalty that moves with each visit.
- Ingredient costs and suppliers, for the trade-war scenario. Items currently
  carry a sticker `price` only, with no cost side, so margin can't be computed.
