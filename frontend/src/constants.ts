import type { Bakery, Daypart } from './types'

export const BAKERY_LABELS: Record<Bakery, string> = {
  grandmas_bakeria: "Grandma's Bakeria",
  the_bakery: 'The Bakery',
}

export const DAYPART_LABELS: Record<Daypart, string> = {
  early_morning: 'Early morning',
  morning: 'Morning',
  lunch: 'Lunch',
  afternoon: 'Afternoon',
  evening: 'Evening',
}

export const DAYPARTS = Object.keys(DAYPART_LABELS) as Daypart[]
