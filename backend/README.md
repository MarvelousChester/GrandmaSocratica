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
uv run python run_simulation.py           # fuller report on a random day; --seed N replays one
uv run python run_simulation.py --seed 0 --json ../frontend/sample_data/day_seed0.json
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
| `POST /api/simulate` | one standalone day for the menus in the body (`{menus, seed?}`), for the frontend's editor; see below |
| `GET /season?through=N` | days 0..N as a timeline: each day's `prices`, `usual_prices`, average `habit`, `summary`, `ledger` and The Bakery's `repricings`, plus the `rivalries` it tracks |

`POST /api/simulate` sits outside the season: it simulates the menus it is
sent, as-is, with no competitor repricing or habits. Without a `seed` every
call is a different day (same town, fresh arrivals and choices); the seed
used is in `config.seed`, and sending it back replays that day exactly. Customers still expect
the base menu prices (items not on the base menus are taken at face value),
and seed 0 with the base menus gives exactly day 0. Two menus for one bakery,
an item on another bakery's menu, or a repeated item id is a 422. Items
without a recipe sell normally and are listed in `ledger.uncosted_items`.

`GET /days/{day}/menu` shows both menus as they stood that day, competitor
prices included. A database created before days counted from 0 rejects a
day-0 profile; delete `grandma.db` to recreate it.

The ledger has an entry per bakery with the day's `financials` (`units_sold`,
`revenue`, `ingredient_cost`, `profit`) and `ingredients` used (`grams`,
`cost`, costliest first), and the same two blocks for every opening hour in
`hourly`, plus `financials` for every menu item in `items` (by item id, zero
for items that didn't sell). Costs come from `menu/recipes_seed.py` and use that day's menu, so a
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
  (commuter, lunch worker, student, regular, after-work in
  `customers/presets.py`). Each
  segment has a share and a distribution spec (`normal`, `beta`, `uniform`,
  `constant`) per trait, and the whole config round-trips through JSON.
- **Arrivals** — each customer visits with their own probability, at their
  preferred minute plus jitter. Arrivals outside opening hours don't happen.
- **Choice** — a multinomial logit over every allergen-safe item on both menus
  plus "buy nothing". Utility is a sum of taste match, flavour-category
  affinity, daypart appeal (blended between neighbouring dayparts), log price,
  price markup, log portion, bakery bias and habit. Each purchase records its
  `UtilityBreakdown`. "Buy nothing" scores `no_purchase_utility` (2.5), so
  about a fifth of visitors leave empty-handed on opening day, more when
  prices rise or nothing suits the hour.
- **Price response** — customers expect each item's usual price
  (`DayConfig.usual_prices`; a season starts from the base menu prices).
  Charging more costs `markup * price_sensitivity * tolerance * (e^(markup% /
  tolerance) - 1)`, so small rises barely register and big ones are
  dealbreakers; discounts help linearly. With the defaults (`markup` 0.5,
  `markup_tolerance` 0.07), averaged over 30 days for the Fall Parfait:

  | price change | +2% | +5% | +10% | +20% | +30% | +50% |
  |---|---|---|---|---|---|---|
  | sales change | −4% | −9% | −20% | −51% | −86% | −99% |

  That is the first-day shock; over a season customers get used to new prices
  (see Customer memory).

## Customer memory

Over a season, customers carry two things from one day to the next
(`simulation/season.py`, `simulation/habits.py`):

- **Usual prices drift** toward what was charged, closing `price_memory`
  (5%) of the gap each day. A rise hurts most at first and is slowly
  accepted; a long discount makes the old price feel like a markup when it
  returns. A 30% rise across grandma's menu drops her share from about 46% to
  14% on the day, and it is back near 40% three weeks later.
- **Habits** — each purchase adds `gain` (0.1) to that customer's habit for
  the bakery, and every habit keeps `retention` (90%) of itself daily, so a
  daily buyer levels off at 1.0 utility. Customers won by a price cut stay a
  while after it ends; customers driven off build a habit for The Bakery.

Each `DayRecord` (and `GET /season`) reports the day's `usual_prices` and the
town's average `habit` per bakery; `GET /days/{day}/simulation` carries every
customer's habits in `config.habits` and a `habit` term in each breakdown.
Set `price_memory=0` and `habits.gain=0` for memoryless days.

## Competitor pricing

Over a run of days, The Bakery reprices in response to grandma. Run it with:

```bash
uv run python run_season.py --days 28 --cut fall_parfait=6.50@2
```

Every run also simulates the same season with The Bakery frozen, so the report
shows what grandma keeps against what the response takes back, in both share
and gross profit.

Those two figures are averaged over `--seeds` seasons (5 by default), because
one season's difference is well inside day-to-day noise -- on a single seed the
sign flips roughly one time in six. The narrative sections (what moved, and
why) come from the first seed; only the numbers are pooled. Pass recipe books to `SeasonSimulator` and each `DayRecord`
carries that day's `ledger`; `SeasonResult.profit_series(bakery)` reads it.

**Who watches whom** (`competition/rivalry.py`) — pairs are found by taste, not
declared by hand: each of The Bakery's items tracks the nearest item on
grandma's menu, using the flavour meters plus a penalty for not sharing
categories (the meters alone can't separate a lemon square from a pumpkin
parfait). Add an item and it starts competing automatically.

The map is refreshed at every review, not fixed at opening, so reformulating an
item moves what it competes with. Make the Fall Parfait savoury and The
Bakery's parfait stops shadowing it:

```bash
uv run python run_season.py --days 21 --sweeten fall_parfait=-0.85@3
#   day 7  Autumn Parfait switched from Fall Parfait to Morning Bun
```

Grandma's signature then has nothing tracking it at all -- reformulating away
from the knock-off is a way out of the price fight rather than into it.

**How they respond** (`competition/pricing.py`) — three separate delays sit
between grandma's move and the answer, which is what makes it read as a real
competitor rather than a mirror:

| knob | what it models | default |
|---|---|---|
| `observation_lag_days` | they act on the price they last *saw*; competitor checks happen on a round | 4 |
| `review_every_days` | prices only move on review day — approvals, reprinted boards | 7 |
| `adjustment_rate` | they close part of the gap, not all of it; jumping straight there makes both shops oscillate | 0.4 |
| `min_margin_pct` | the margin they refuse to sell under, over today's cost | 0.10 |

They watch grandma's posted prices (stale) and their own till (current). Share
of each rivalry pair decides *whether* they act at all:

- below `losing_below` (50%) they cut toward `undercut` (12%) under her price
- above `harvesting_above` (65%) they raise instead — a chain that's winning
  harvests margin rather than chasing
- in between they hold

**What stops them** — the floor under every price is what the item costs them
*today*, from their own recipe book at that day's ingredient prices, plus
`min_margin_pct` (10%; set it to 0 for exactly break-even). They will not
undercut themselves into a loss however hard grandma cuts, and the floor moves
on its own when ingredient prices move or a recipe is sweetened.

That floor also pushes the other way. If a spike puts an item under water they
raise to clear cost at the next review **whether or not they are winning** — a
`cost_floor` move, taken straight to the floor rather than eased in, and it
beats the price ceiling when costs really run away. A cream spike alone is
enough to force their parfait up, which hands grandma a couple of points of
share the week it lands -- though habit pulls those customers back after:

```bash
uv run python run_season.py --days 21 --spike cream=12@5
#   day 7  Autumn Parfait  $6.95 -> $8.49  cost_floor
#   Autumn Parfait now costs them $7.36; below $8.18 they lose money
```

Prices are otherwise capped at `price_ceiling_pct` of their opening price and
snapped to menu-board endings (`.95`/`.49`, never below the floor). Grandma
never auto-reacts — she's the player, and two reactive sides would run away
into a price war.

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
      presets.py       default five-segment population
    choice/
      utility.py       UtilityWeights, UtilityModel.score() -> UtilityBreakdown
      model.py         ChoiceConfig, ChoiceModel (logit), Choice
    simulation/
      events.py        VisitEvent, DaySummary
      day.py           DayConfig, DaySimulator.run() -> DayResult
      ledger.py        DayLedger — revenue, ingredient cost, profit, usage; per day and hour
      habits.py        HabitConfig.update() — per-customer habits carried between days
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
- Reputation: habits only form through buying, so a bakery can't win
  customers who have never visited it by word of mouth.
- Store hours per bakery. `DayClock` has one global open/close, so grandma
  can't open earlier to take the commuter rush she currently loses.
- Habits make every purchase likelier, not just one bakery's, so walk-aways
  fall from about 21% to 13% over four weeks with no change in prices.
