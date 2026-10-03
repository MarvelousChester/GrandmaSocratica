import menusFile from '../sample_data/menus.json'
import type { Allergen, Bakery, FlavorCategory, ItemCategory, MenuItem, MenusFile } from './types'

// Regenerate from the seed menus with grandma_sim.menu.seed.build_menus() if the
// backend menus change. Swap this import for a fetch once there is an API.
const data = menusFile as unknown as MenusFile

export const CLOCK = data.clock
export const MENUS = data.menus

// `name` is possessive for menu titles ("The Bakery's Menu"); `label` names the shop.
export const BAKERY_INFO: Record<Bakery, { name: string; label: string; roof: string; wall: string }> = {
  the_bakery: { name: "The Bakery's", label: 'The Bakery', roof: '#ef8c8c', wall: '#f8c9c9' },
  grandmas_bakeria: { name: "Grandma's", label: "Grandma's", roof: '#86d886', wall: '#bef2c4' },
}

// Left to right on screen.
export const PANEL_ORDER: Bakery[] = ['the_bakery', 'grandmas_bakeria']

// Reports list Grandma first: she's who the player is rooting for.
export const REPORT_ORDER: Bakery[] = ['grandmas_bakeria', 'the_bakery']

export const WALKAWAY_FILL = '#d9d4cf'

export const shop = (bakery: Bakery) => BAKERY_INFO[bakery].label

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

/** 1234.5 -> "$1,234.50" */
export const formatMoney = (dollars: number) =>
  dollars.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

/** 0.451 -> "45%" */
export const formatPercent = (share: number) => `${Math.round(share * 100)}%`

/** Hour of day as a short 12-hour label, e.g. 13 -> "1 PM". */
export const formatHour = (hour: number) => `${hour % 12 || 12} ${hour % 24 < 12 ? 'AM' : 'PM'}`

// Customer segments (backend/grandma_sim/customers/presets.py) as plural nouns.
const SEGMENT_PEOPLE: Record<string, string> = {
  commuter: 'commuters',
  lunch_worker: 'lunch workers',
  student: 'students',
  regular: 'regulars',
  after_work: 'after-work crowd',
}

/** 'lunch_worker' -> 'lunch workers'; unknown segments fall back to their name. */
export const segmentPeople = (segment: string) =>
  SEGMENT_PEOPLE[segment] ?? humanize(segment).toLowerCase()

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
