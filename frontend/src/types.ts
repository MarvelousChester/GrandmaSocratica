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
