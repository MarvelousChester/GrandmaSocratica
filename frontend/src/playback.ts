// Turns a simulated day into what's on screen at a given minute: where each
// customer is, and how each bakery is doing so far. Pure functions, no React.
import type { Bakery, DayResult, VisitEvent } from './types'

/** Simulated minutes per real second at 1×. */
export const SPEED_MIN_PER_SEC = 5

// Durations below are in simulated minutes, so walking stays in step with the
// clock whatever the speed.
export const WALK = 3 // edge -> door, and door -> edge
export const INSIDE = 2 // a buyer is inside the shop
const FADE = 0.4
const POP = 4 // a sale's "+$" floats above the door

// Scene geometry, in the Scene SVG's viewBox units.
export const DOOR_X: Record<Bakery, number> = { the_bakery: 610, grandmas_bakeria: 1158 }
export const GROUND_Y = 1040 // top of the sidewalk
export const VIEW_W = 1700
export const VIEW_H = 1288

/** Stable 0..1 value per customer, so jitter and choices don't change between frames. */
export function hash(id: string): number {
  let h = 2166136261
  for (let i = 0; i < id.length; i++) h = Math.imul(h ^ id.charCodeAt(i), 16777619)
  return (h >>> 0) / 4294967296
}

/** Where a customer heads: their bakery, or one picked by hash if they walk away. */
export function targetOf(event: VisitEvent): Bakery {
  return event.choice.bakery ?? (hash(event.customer_id) < 0.5 ? 'the_bakery' : 'grandmas_bakeria')
}

/** Last minute a customer is on screen, relative to their event. */
export const leaveAfter = (event: VisitEvent) => (event.choice.purchased ? INSIDE + WALK : WALK)

export interface PersonPose {
  x: number
  opacity: number
  facing: 1 | -1 // 1 = right, -1 = left
}

/**
 * Where `event`'s customer stands at `minute`, or null if off screen.
 *
 * They walk in from the edge on their bakery's side and reach the door at
 * their event time. A buyer fades into the shop, stays inside, fades back out
 * and walks back; a walk-away turns round at the door.
 *
 * Args:
 *  edges: x just off the visible left and right edges.
 */
export function personAt(
  event: VisitEvent,
  minute: number,
  edges: { left: number; right: number },
): PersonPose | null {
  const t = event.choice.purchased
  const bakery = targetOf(event)
  const door = DOOR_X[bakery] + (hash(event.customer_id + 'x') - 0.5) * 50
  const edge = bakery === 'the_bakery' ? edges.left : edges.right
  const walk = (from: number, to: number, start: number) =>
    from + (to - from) * Math.min(1, Math.max(0, (minute - start) / WALK))
  const toDoor: PersonPose['facing'] = door > edge ? 1 : -1
  const away: PersonPose['facing'] = toDoor === 1 ? -1 : 1

  const dt = minute - event.minute
  if (dt < -WALK || dt > leaveAfter(event)) return null
  if (dt <= 0) {
    // Walking in; a buyer starts fading as they reach the door.
    const opacity = t ? Math.min(1, -dt / FADE) : 1
    return { x: walk(edge, door, event.minute - WALK), opacity, facing: toDoor }
  }
  if (!t) return { x: walk(door, edge, event.minute), opacity: 1, facing: away }
  if (dt < INSIDE) return { x: door, opacity: Math.max(0, (dt - INSIDE + FADE) / FADE), facing: away }
  return { x: walk(door, edge, event.minute + INSIDE), opacity: 1, facing: away }
}

/** How far (0..1) a purchase's "+$" has floated up at `minute`, or null when it isn't showing. */
export function popAt(event: VisitEvent, minute: number): number | null {
  const t = (minute - event.minute) / POP
  return event.choice.purchased && t >= 0 && t <= 1 ? t : null
}

export interface BakeryMetrics {
  revenue: number
  sold: number
  profit: number | null // null without a ledger
}

/**
 * Each bakery's totals from purchases made by `minute`.
 *
 * Revenue and units are exact. The ledger only has cost per hour, so the
 * current hour's cost is pro-rated by units sold so far in it; profit is exact
 * at every hour boundary and at the end of the day.
 */
export function metricsAt(day: DayResult, minute: number): Record<Bakery, BakeryMetrics> {
  const result = {} as Record<Bakery, BakeryMetrics>
  const hour = Math.floor(minute / 60)
  for (const bakery of ['the_bakery', 'grandmas_bakeria'] as Bakery[]) {
    let revenue = 0
    let sold = 0
    let soldThisHour = 0
    for (const e of day.events) {
      if (e.minute > minute) break
      if (e.choice.bakery !== bakery) continue
      revenue += e.choice.price
      sold += 1
      if (Math.floor(e.minute / 60) === hour) soldThisHour += 1
    }

    let profit: number | null = null
    const ledger = day.ledger?.bakeries[bakery]
    if (ledger) {
      let cost = 0
      for (const h of ledger.hourly) {
        if (h.hour < hour) cost += h.financials.ingredient_cost
        else if (h.hour === hour && h.financials.units_sold > 0) {
          cost += h.financials.ingredient_cost * (soldThisHour / h.financials.units_sold)
        }
      }
      // Once every hour is in, use the ledger's own total (hourly costs are rounded).
      const lastHour = ledger.hourly.at(-1)?.hour ?? -1
      profit = hour > lastHour ? ledger.financials.profit : revenue - cost
    }
    result[bakery] = { revenue, sold, profit }
  }
  return result
}

/** When playback stops: closing time, or once the last customer has left. */
export function dayEnd(day: DayResult): number {
  const last = day.events.at(-1)
  return Math.max(day.config.clock.close_minute, last ? last.minute + leaveAfter(last) : 0)
}
