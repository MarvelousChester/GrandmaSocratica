import menusFile from '../sample_data/menus.json'
import type { Allergen, Bakery, FlavorCategory, ItemCategory, MenuItem, MenusFile } from './types'

// Regenerate from the seed menus with grandma_sim.menu.seed.build_menus() if the
// backend menus change. Swap this import for a fetch once there is an API.
const data = menusFile as unknown as MenusFile

export const CLOCK = data.clock
export const MENUS = data.menus

export const BAKERY_INFO: Record<Bakery, { name: string; roof: string; wall: string }> = {
  the_bakery: { name: "The Bakery's", roof: '#ef8c8c', wall: '#f8c9c9' },
  grandmas_bakeria: { name: "Grandma's", roof: '#86d886', wall: '#bef2c4' },
}

// Left to right on screen.
export const PANEL_ORDER: Bakery[] = ['the_bakery', 'grandmas_bakeria']

/** Minutes since midnight as a 12-hour clock, e.g. 360 -> "6:00 AM". */
export function formatTime(minute: number): string {
  const h24 = Math.floor(minute / 60) % 24
  const m = Math.floor(minute % 60)
  return `${h24 % 12 || 12}:${String(m).padStart(2, '0')} ${h24 < 12 ? 'AM' : 'PM'}`
}

// Option lists mirror backend/grandma_sim/core/enums.py.
export const ITEM_CATEGORIES: ItemCategory[] = ['pastry', 'cake', 'dessert', 'bread', 'sandwich', 'drink']

export const FLAVOR_CATEGORIES: FlavorCategory[] = [
  'chocolate', 'vanilla', 'caramel', 'fruit', 'berry', 'citrus', 'nut',
  'coffee', 'spice', 'herbal', 'floral', 'cheese', 'savoury',
]

export const ALLERGENS: Allergen[] = ['gluten', 'dairy', 'egg', 'tree_nut', 'peanut', 'soy', 'sesame']

/** 'tree_nut' -> 'Tree nut' */
export function humanize(value: string): string {
  const text = value.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** Starting point for the "Add menu item" form. `id` is assigned on save. */
export function blankItem(bakery: Bakery): MenuItem {
  return {
    id: '',
    name: '',
    bakery,
    category: 'pastry',
    description: '',
    flavor: { sweet_savoury: 0, bitterness: 0, fruitiness: 0, categories: [] },
    price: 5,
    portion_size_g: 100,
    allergens: [],
    // Not user-editable. The backend treats unlisted dayparts as 0.5.
    daypart_weights: {},
  }
}

/** 'Ham & Cheese' -> 'ham_cheese', suffixed with _2, _3... if already taken. */
export function newItemId(name: string, taken: Set<string>): string {
  const base = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'item'
  let id = base
  for (let n = 2; taken.has(id); n++) id = `${base}_${n}`
  return id
}
