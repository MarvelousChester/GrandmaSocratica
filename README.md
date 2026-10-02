# Grandma's Bakeria — menu backend

The menu half of the sim: what each bakery sells and what each item is like.
The customer-profile weights live elsewhere and read from here.

## Run it

```bash
python3 -m backend.store     # creates ./grandma.db, seeds 6 items per bakery
```

Python 3.11+ and `pydantic>=2`. The DB is gitignored — rebuild any time, it's
generated from `backend/seed.py`.

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

Add items in `backend/seed.py` and re-run the build.

## Layout

```
backend/
  enums.py   allergens, dayparts, flavour categories, item categories, bakeries
  flavor.py  FlavorProfile — the meters, distance(), category_overlap()
  items.py   MenuItem, Menu
  seed.py    both menus
  store.py   SQLite schema, read/write, menu_rows()
```

## Not done yet

- Demand/tick loop — items know their appeal per daypart, nothing consumes it.
- Ingredient costs and suppliers, for the trade-war scenario. Items currently
  carry a sticker `price` only, with no cost side, so margin can't be computed.
