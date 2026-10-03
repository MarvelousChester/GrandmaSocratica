// Mirrors backend/enums.py and backend/items.py (pydantic models serialised to JSON).

export type Allergen =
  | 'gluten'
  | 'dairy'
  | 'egg'
  | 'tree_nut'
  | 'peanut'
  | 'soy'
  | 'sesame'

export type FlavorCategory =
  | 'chocolate'
  | 'vanilla'
  | 'caramel'
  | 'fruit'
  | 'berry'
  | 'citrus'
  | 'nut'
  | 'coffee'
  | 'spice'
  | 'herbal'
  | 'floral'
  | 'cheese'
  | 'savoury'

export type Daypart =
  | 'early_morning'
  | 'morning'
  | 'lunch'
  | 'afternoon'
  | 'evening'

export type ItemCategory =
  | 'pastry'
  | 'cake'
  | 'dessert'
  | 'bread'
  | 'sandwich'
  | 'drink'

export type Bakery = 'grandmas_bakeria' | 'the_bakery'

export interface FlavorProfile {
  sweet_savoury: number // -1 savoury .. +1 sweet
  bitterness: number // 0..1
  fruitiness: number // 0..1
  categories: FlavorCategory[]
}

export interface MenuItem {
  id: string
  name: string
  bakery: Bakery
  category: ItemCategory
  description: string
  flavor: FlavorProfile
  price: number // dollars
  portion_size_g: number
  allergens: Allergen[]
  daypart_weights: Partial<Record<Daypart, number>> // unlisted = 0.5
}

// Mirrors backend/grandma_sim/core/clock.py. Times are minutes since midnight.
export interface DayClock {
  open_minute: number
  close_minute: number
  daypart_starts: Record<Daypart, number>
}

// sample_data/menus.json: the seed menus plus the default clock.
export interface MenusFile {
  clock: DayClock
  menus: Record<Bakery, MenuItem[]>
}

// ---- simulate API: mirrors backend/grandma_sim (Menu, DayResult and friends) ----

export interface Menu {
  bakery: Bakery
  items: MenuItem[]
}

export interface SimulateRequest {
  menus: Menu[]
  seed?: number // omitted = a random day; the seed used comes back in config.seed
}

export interface UtilityBreakdown {
  taste: number
  category: number
  daypart: number
  price: number
  markup: number
  portion: number
  bakery: number
  habit: number
  total: number
}

/** What one customer did. `purchased` is false for a walk-away (item fields are null). */
export interface Choice {
  item_id: string | null
  item_name: string | null
  bakery: Bakery | null
  price: number
  probability: number
  breakdown: UtilityBreakdown | null
  purchased: boolean
}

/** One customer arriving and deciding. `events` is the day's schedule, in time order. */
export interface VisitEvent {
  minute: number // since midnight
  time: string // 'HH:MM'
  daypart: Daypart
  customer_id: string
  segment: string
  choice: Choice
}

export interface BakeryTotals {
  purchases: number
  revenue: number
}

export interface DaySummary {
  visits: number
  walkaways: number
  purchases: number
  by_bakery: Record<Bakery, BakeryTotals>
  item_sales: Record<string, number>
}

/** Mirrors backend/grandma_sim/simulation/ledger.py. Cost is ingredients only. */
export interface Financials {
  units_sold: number
  revenue: number
  ingredient_cost: number
  profit: number
}

export interface IngredientUsage {
  name: string
  price_per_kg: number
  grams: number
  cost: number
}

export interface LedgerPeriod {
  financials: Financials
  ingredients: Record<string, IngredientUsage> // by ingredient id, costliest first
}

export interface BakeryLedger extends LedgerPeriod {
  hourly: (LedgerPeriod & { hour: number })[]
  items: Record<string, Financials> // by item id, every item on the menu
}

export interface DayLedger {
  bakeries: Record<Bakery, BakeryLedger>
  uncosted_items: string[] // items with no recipe; sold, but no cost counted
}

export interface DayResult {
  config: { seed: number; clock: DayClock }
  menus: Menu[]
  customers: { id: string; segment: string }[] // plus taste traits the UI doesn't use yet
  events: VisitEvent[]
  summary: DaySummary
  ledger: DayLedger | null
}
