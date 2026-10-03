import type { Bakery, DayResult, IngredientUsage } from './types'

const BAKERIES: Bakery[] = ['grandmas_bakeria', 'the_bakery']

export interface ItemRow {
  id: string
  name: string
  bakery: Bakery
  price: number
  sold: number
  revenue: number
  cost: number | null // ingredients for the units sold; null without a recipe or ledger
  profit: number | null
  byHour: number[] // units sold in each of the report's hours
}

export interface BakeryReport {
  sold: number
  revenue: number
  cost: number | null // null when the day came back without a ledger
  profit: number | null
  share: number // of all purchases, 0..1
  items: ItemRow[] // best seller first
  ingredients: IngredientUsage[] // costliest first
}

export interface HourRow {
  hour: number // 7 = 7:00-8:00
  sold: Record<Bakery, number>
  walkaways: number
}

export interface SegmentRow {
  segment: string
  visits: number
  sold: Record<Bakery, number>
  walkaways: number
}

export interface DayReport {
  seed: number
  visits: number
  purchases: number
  walkaways: number
  bakeries: Record<Bakery, BakeryReport>
  hours: HourRow[]
  segments: SegmentRow[] // most visits first
  uncosted: string[]
}

const perBakery = (): Record<Bakery, number> => ({ grandmas_bakeria: 0, the_bakery: 0 })

/** Turns a simulated day into the figures both report views show. */
export function buildReport(day: DayResult): DayReport {
  const { summary, ledger, events, config } = day
  const firstHour = Math.floor(config.clock.open_minute / 60)
  const hourCount = Math.ceil(config.clock.close_minute / 60) - firstHour
  const uncosted = new Set(ledger?.uncosted_items ?? [])

  const items: ItemRow[] = day.menus.flatMap((menu) =>
    menu.items.map((item) => {
      const sold = summary.item_sales[item.id] ?? 0
      const money = uncosted.has(item.id) ? undefined : ledger?.bakeries[menu.bakery].items[item.id]
      return {
        id: item.id,
        name: item.name,
        bakery: menu.bakery,
        price: item.price,
        sold,
        revenue: sold * item.price,
        cost: money ? money.ingredient_cost : null,
        profit: money ? money.profit : null,
        byHour: Array<number>(hourCount).fill(0),
      }
    }),
  )
  const itemsById = new Map(items.map((i) => [i.id, i]))

  const bakeries = Object.fromEntries(
    BAKERIES.map((bakery) => {
      const totals = summary.by_bakery[bakery]
      const money = ledger?.bakeries[bakery]
      const report: BakeryReport = {
        sold: totals.purchases,
        revenue: totals.revenue,
        cost: money ? money.financials.ingredient_cost : null,
        profit: money ? money.financials.profit : null,
        share: summary.purchases ? totals.purchases / summary.purchases : 0,
        items: items.filter((i) => i.bakery === bakery).sort((a, b) => b.sold - a.sold),
        ingredients: money ? Object.values(money.ingredients) : [],
      }
      return [bakery, report]
    }),
  ) as Record<Bakery, BakeryReport>

  const hours: HourRow[] = Array.from(
    { length: hourCount },
    (_, i) => ({ hour: firstHour + i, sold: perBakery(), walkaways: 0 }),
  )
  const segments = new Map<string, SegmentRow>()

  // Tally each visit into its hour, its customer's segment and the item bought.
  for (const event of events) {
    const hourIndex = Math.floor(event.minute / 60) - firstHour
    const hour = hours[hourIndex]
    let segment = segments.get(event.segment)
    if (!segment) {
      segment = { segment: event.segment, visits: 0, sold: perBakery(), walkaways: 0 }
      segments.set(event.segment, segment)
    }
    segment.visits += 1
    const { bakery } = event.choice
    if (bakery) {
      hour.sold[bakery] += 1
      segment.sold[bakery] += 1
      const item = itemsById.get(event.choice.item_id ?? '')
      if (item) item.byHour[hourIndex] += 1
    } else {
      hour.walkaways += 1
      segment.walkaways += 1
    }
  }

  return {
    seed: config.seed,
    visits: summary.visits,
    purchases: summary.purchases,
    walkaways: summary.walkaways,
    bakeries,
    hours,
    segments: [...segments.values()].sort((a, b) => b.visits - a.visits),
    uncosted: ledger?.uncosted_items ?? [],
  }
}

export const hourVisits = (h: HourRow) => h.sold.grandmas_bakeria + h.sold.the_bakery + h.walkaways

/** The hour with the most visitors, or null on an empty day. */
export function busiestHour(report: DayReport): HourRow | null {
  const busiest = report.hours.reduce((best, h) => (hourVisits(h) > hourVisits(best) ? h : best), report.hours[0])
  return busiest && hourVisits(busiest) > 0 ? busiest : null
}