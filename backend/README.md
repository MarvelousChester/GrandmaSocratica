# Grandma's Bakeria — backend

The `grandma_sim` package: both bakeries' menus, the generated customer
population, the choice model, and the whole-day simulation.

## Run it

All commands run from `backend/`:

```bash
uv sync                                   # Python 3.11+, pydantic, numpy, fastapi
uv run python -m grandma_sim.api          # serves the API on http://127.0.0.1:8000 (docs at /docs)
uv run python -m grandma_sim.menu.store   # rebuilds ./grandma.db from the seed menus
uv run python -m grandma_sim.simulation   # simulates one day, prints totals (optional seed arg)
uv run python run_simulation.py           # fuller report; --seed, --customers, --events
uv run python run_simulation.py --json ../frontend/sample_data/day_seed0.json
```

The DB is gitignored and generated from `grandma_sim/menu/seed.py`; the API
seeds it on first start. Rebuilding with `menu.store` deletes the file, which
also wipes any day profiles set through the API.

## API

Days are numbered from 0 (opening day) and form one continuous season: day N
is simulated after days 0..N-1, so The Bakery's repricing in response to
grandma's earlier prices (see Competitor pricing) is already applied. Each day
has the same customers (fixed `population_seed`) and its number as the seed
for arrivals and choices, so it is reproducible, and changing a profile only
changes decisions, never who shows up. Days are cached; changing a profile
only re-simulates the days from it onward. The API and `run_season.py` give
identical days for the same profiles.

| endpoint | |
|---|---|
| `GET /menu` | base menu items, both bakeries, as a flat list |
| `PUT /days/{day}/profile` | set the profile from `day` onward (body below) |
| `GET /days/{day}/profile` | profile in force on `day`; `source_day` says which day set it (`null` = base menus) |
| `DELETE /days/{day}/profile` | drop the profile set on `day`; the previous one carries over again |
| `GET /profiles` | every day that has a profile set |
| `GET /days/{day}/menu` | menu items as they stand on `day` |
| `GET /days/{day}/simulation` | the simulated day: `config`, `menus`, `customers`, `events`, `summary`, `ledger` |
| `GET /days/{day}/ledger` | just the day's costs, profit and ingredient usage |
| `GET /season?through=N` | days 0..N as a timeline: each day's `prices`, `summary`, `ledger` and The Bakery's `repricings`, plus the `rivalries` it tracks |

`GET /days/{day}/menu` shows both menus as they stood that day, competitor
prices included. A database created before days counted from 0 rejects a
day-0 profile; delete `grandma.db` to recreate it.

The ledger has an entry per bakery with the day's `financials` (`units_sold`,
`revenue`, `ingredient_cost`, `profit`) and `ingredients` used (`grams`,
`cost`, costliest first), and the same two blocks for every opening hour in
`hourly`. Costs come from `menu/recipes_seed.py` and use that day's menu, so a
portion override changes ingredient usage. Cost is ingredients only — no
labour or rent yet.

A profile carries forward: set on day 3, it applies to days 3, 4, 5… until a
later day sets its own. It lists only what differs from the base menu, by item
id; any field left out keeps its base value:

```json
{
  "items": {
    "fall_parfait":      { "price": 6.50 },
    "gruyere_croissant": { "flavor": { "sweet_savoury": 0.2 } },
    "mocha_latte":       { "available": false }
  }
}
```

Overridable fields: `price`, `portion_size_g`, `flavor` (`sweet_savoury`,
`bitterness`, `fruitiness`, `categories`), `allergens`, `daypart_weights`,
`available`. Unknown item ids or out-of-range values return 422.

### Ingredient prices

Ingredient prices have their own schedule, independent of menu profiles, with
the same carry-forward rule — so a menu change never wipes a price shock.
They only change costs (the ledger), not what customers buy.

| endpoint | |
|---|---|
| `GET /ingredients` | base ingredient prices per bakery (`price_per_kg`) |
| `PUT /days/{day}/ingredient-prices` | set ingredient prices from `day` onward (body below) |
| `GET /days/{day}/ingredient-prices` | the changes in force on `day`, with `source_day` |
| `DELETE /days/{day}/ingredient-prices` | drop them; the previous ones carry over again |
| `GET /ingredient-prices` | every day that has ingredient prices set |
| `GET /days/{day}/ingredients` | each bakery's ingredient prices as they stand on `day` |

```json
{
  "multipliers": { "butter": 1.5 },
  "prices": { "grandmas_bakeria": { "flour": 2.10 } }
}
```

`multipliers` scale an ingredient's price at every bakery (a market-wide
shortage); `prices` set one bakery's $/kg outright and win over a multiplier.
Unknown ingredients or bakeries, or negative values, return 422. The ledger's
ingredient entries include the `price_per_kg` paid that day.

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
  price markup, log portion and bakery bias. Each purchase records its
  `UtilityBreakdown`.
- **Price response** — customers expect each item's usual price
  (`DayConfig.usual_prices`; the API and season use the base menu prices).
  Charging more costs `markup * price_sensitivity * tolerance * (e^(markup% /
  tolerance) - 1)`, so small rises barely register and big ones are
  dealbreakers; discounts help linearly. With the defaults (`markup` 0.5,
  `markup_tolerance` 0.07), averaged over 30 days for the Fall Parfait:

  | price change | +2% | +5% | +10% | +20% | +30% | +50% |
  |---|---|---|---|---|---|---|
  | sales change | −2% | −6% | −15% | −45% | −79% | −99% |

## Competitor pricing

Over a run of days, The Bakery reprices in response to grandma. Run it with:

```bash
uv run python run_season.py --days 28 --cut fall_parfait=6.50@2
```

Every run also simulates the same season with The Bakery frozen, so the report
shows what grandma keeps against what the response takes back, in both share
and gross profit. Pass recipe books to `SeasonSimulator` and each `DayRecord`
carries that day's `ledger`; `SeasonResult.profit_series(bakery)` reads it.

**Who watches whom** (`competition/rivalry.py`) — pairs are found by taste, not
declared by hand: each of The Bakery's items tracks the nearest item on
grandma's menu, using the flavour meters plus a penalty for not sharing
categories (the meters alone can't separate a lemon square from a pumpkin
parfait). Add an item and it starts competing automatically.

**How they respond** (`competition/pricing.py`) — three separate delays sit
between grandma's move and the answer, which is what makes it read as a real
competitor rather than a mirror:

| knob | what it models | default |
|---|---|---|
| `observation_lag_days` | they act on the price they last *saw*; competitor checks happen on a round | 4 |
| `review_every_days` | prices only move on review day — approvals, reprinted boards | 7 |
| `adjustment_rate` | they close part of the gap, not all of it; jumping straight there makes both shops oscillate | 0.4 |

They watch grandma's posted prices (stale) and their own till (current). Share
of each rivalry pair decides *whether* they act at all:

- below `losing_below` (50%) they cut toward `undercut` (12%) under her price
- above `harvesting_above` (65%) they raise instead — a chain that's winning
  harvests margin rather than chasing
- in between they hold

Prices are clamped to a floor and ceiling around their opening price and
snapped to menu-board endings (`.95`/`.49`). Grandma never auto-reacts — she's
the player, and two reactive sides would run away into a price war.

**Running the days** (`simulation/season.py`) — `SeasonSimulator` holds the
population fixed (one `population_seed`) and re-rolls arrivals and decisions
each day, so a swing in share is attributable to the prices rather than to a
different crowd. Grandma's moves are `DayProfile`s, the same overrides the API
serves, carried forward until a later day replaces them; The Bakery's responses
are layered on top so the player's profile never wipes a price it set.

## Layout

```
backend/
  pyproject.toml, uv.lock
  run_simulation.py    run a day and print a report, optionally write JSON
  run_season.py        run N days with The Bakery reacting, vs a frozen baseline
  grandma_sim/
    core/
      enums.py         allergens, dayparts, flavour categories, item categories, bakeries
      flavor.py        FlavorProfile — the meters, distance(), category_overlap()
      clock.py         DayClock — opening hours, minute -> daypart, daypart blending
    menu/
      items.py         MenuItem, Menu
      seed.py          both menus
      store.py         SQLite schema, read/write, menu_rows()
      costing.py       Ingredient, Pantry, Recipe, RecipeBook — what an item costs to make
      recipes_seed.py  ingredient prices and recipes for the seed menus
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
      ledger.py        DayLedger — revenue, ingredient cost, profit, usage; per day and hour
      season.py        SeasonConfig, SeasonSimulator.run() -> SeasonResult
    competition/
      rivalry.py       find_rivalries() — which item tracks which, by taste
      pricing.py       PricingPolicy, CompetitorPricer.review() -> Repricing
    profiles/
      overrides.py     ItemOverride, FlavorOverride, DayProfile.apply(menus)
      ingredients.py   IngredientPrices.apply(recipe_books) — per-day ingredient prices
      store.py         ScheduleStore — day-scheduled settings in SQLite, carry-forward lookup
    api/
      service.py       SimulationService — base menus + profiles -> simulated day
      app.py           FastAPI routes, create_app()
```

## Not done yet

- Baskets (one item per visit for now), inventory and queues.
- Multi-day state, e.g. loyalty that moves with each visit.
- Store hours per bakery. `DayClock` has one global open/close, so grandma
  can't open earlier to take the commuter rush she currently loses.
- Usual prices never adapt. A price held for weeks still feels like a markup
  (or a discount) on the last day; customers should get used to it over time.
