import {
  BAKERY_INFO,
  formatHour,
  formatMoney,
  formatPercent,
  humanize,
  REPORT_ORDER as ORDER,
  segmentPeople,
  shop,
  WALKAWAY_FILL,
} from './data'
import { busiestHour, hourVisits, type DayReport, type HourRow } from './report'

type Key = [label: string, fill: string]

/** Colour swatches for each shop, plus walk-aways if shown. */
export function Legend({ walkaways }: { walkaways: boolean }) {
  const keys: Key[] = [
    ...ORDER.map((b): Key => [shop(b), BAKERY_INFO[b].roof]),
    ...(walkaways ? [['Left empty-handed', WALKAWAY_FILL] as Key] : []),
  ]
  return (
    <div className="report-legend">
      {keys.map(([label, fill]) => (
        <span key={label}>
          <i style={{ background: fill }} />
          {label}
        </span>
      ))}
    </div>
  )
}

export function ShareBar({ report }: { report: DayReport }) {
  return (
    <div className="report-share" aria-label="Share of sales">
      {ORDER.map((b) => (
        <div key={b} style={{ flexGrow: Math.max(report.bakeries[b].share, 0.08), background: BAKERY_INFO[b].roof }}>
          {shop(b)} {formatPercent(report.bakeries[b].share)}
        </div>
      ))}
    </div>
  )
}

interface HourlyProps {
  report: DayReport
  markPeak?: boolean
}

const CHART_HEIGHT = 130 // px of the tallest bar

/** Visitors per hour as stacked bars: each shop's sales, then walk-aways. Hover a bar for its numbers. */
export function HourlyChart({ report, markPeak = false }: HourlyProps) {
  const peak = Math.max(1, ...report.hours.map(hourVisits))
  const busiest = markPeak ? busiestHour(report) : null

  return (
    <div className="hours" role="img" aria-label="Customers per hour">
      {report.hours.map((h: HourRow) => {
        const parts: [label: string, count: number, fill: string][] = [
          ...ORDER.map((b): [string, number, string] => [shop(b), h.sold[b], BAKERY_INFO[b].roof]),
          ['Left empty-handed', h.walkaways, WALKAWAY_FILL],
        ]
        const tip = [
          `${formatHour(h.hour)} – ${formatHour(h.hour + 1)}`,
          ...parts.map(([label, n]) => `${label}: ${n}`),
          `Total: ${hourVisits(h)}`,
        ].join('\n')
        return (
          <div key={h.hour} className="hours__col tip" data-tip={tip}>
            {busiest === h && <span className="hours__peak">busiest</span>}
            <div className="hours__bar" style={{ height: (hourVisits(h) / peak) * CHART_HEIGHT }}>
              {parts.map(([label, n, fill]) =>
                n > 0 ? <div key={label} style={{ flexGrow: n, background: fill }} /> : null,
              )}
            </div>
            <span className="hours__label">{h.hour % 2 === 0 ? formatHour(h.hour) : ''}</span>
          </div>
        )
      })}
    </div>
  )
}

interface HeatmapProps {
  report: DayReport
  counts?: boolean // print the number in each cell
}

/** Items down the side, hours across: the darker the cell, the more of that item sold then. */
export function ItemHeatmap({ report, counts = false }: HeatmapProps) {
  const max = Math.max(1, ...ORDER.flatMap((b) => report.bakeries[b].items.flatMap((i) => i.byHour)))
  return (
    <div className="heatmap" style={{ gridTemplateColumns: `fit-content(11em) repeat(${report.hours.length}, 1fr)` }}>
      <span />
      {report.hours.map((h) => (
        <span key={h.hour} className="heatmap__hour">
          {h.hour % 2 === 0 ? formatHour(h.hour) : ''}
        </span>
      ))}
      {ORDER.flatMap((b) =>
        report.bakeries[b].items.map((item) => [
          <span key={item.id} className="heatmap__item">
            <i style={{ background: BAKERY_INFO[b].roof }} />
            {item.name}
          </span>,
          ...item.byHour.map((n, i) => (
            <span
              key={`${item.id}-${i}`}
              className="heatmap__cell tip"
              data-tip={`${item.name}\n${formatHour(report.hours[i].hour)}: ${n} sold`}
              style={{ background: n ? `color-mix(in srgb, ${BAKERY_INFO[b].roof} ${Math.round(25 + (75 * n) / max)}%, white)` : '#fff' }}
            >
              {counts && n > 0 ? n : ''}
            </span>
          )),
        ]),
      )}
    </div>
  )
}

interface Bar {
  key: string
  label: string
  value: number
  fill: string
  text: string // shown at the end of the bar
}

interface BarListProps {
  bars: Bar[]
  max: number // value of a full-width bar, so separate lists can share a scale
  title?: string
}

/** Labelled horizontal bars with their value at the end; an empty track means zero. */
function BarList({ bars, max, title }: BarListProps) {
  return (
    <div className="bar-list">
      {title && <span className="bar-list__title">{title}</span>}
      {bars.map((bar) => (
        <div key={bar.key} className="bar" title={`${bar.label}: ${bar.text}`}>
          <span className="bar__label">{bar.label}</span>
          <div className="bar__track">
            <div style={{ width: `${(Math.max(bar.value, 0) / Math.max(max, 1e-9)) * 100}%`, background: bar.fill }} />
          </div>
          <span className="bar__value">{bar.text}</span>
        </div>
      ))}
    </div>
  )
}

/** Per shop: sales, what the ingredients cost, and the profit left over, on one scale. */
export function MoneyBars({ report }: { report: DayReport }) {
  const max = Math.max(...ORDER.map((b) => report.bakeries[b].revenue))
  return (
    <div className="report-cards">
      {ORDER.map((b) => {
        const { revenue, cost, profit } = report.bakeries[b]
        const bars: Bar[] = [
          { key: 'sales', label: 'Sales', value: revenue, fill: BAKERY_INFO[b].wall, text: formatMoney(revenue) },
        ]
        if (cost !== null && profit !== null) {
          bars.push(
            { key: 'cost', label: 'Ingredients', value: cost, fill: WALKAWAY_FILL, text: `− ${formatMoney(cost)}` },
            { key: 'profit', label: 'Profit', value: profit, fill: BAKERY_INFO[b].roof, text: formatMoney(profit) },
          )
        }
        return <BarList key={b} title={shop(b)} bars={bars} max={max} />
      })}
    </div>
  )
}

/** Per kind of customer: one bar split into where they bought, with the count in each part. */
export function CrowdBars({ report }: { report: DayReport }) {
  const max = Math.max(1, ...report.segments.map((s) => s.visits))
  return (
    <div className="bar-list">
      {report.segments.map((s) => {
        const parts: [string, number, string][] = [
          ...ORDER.map((b): [string, number, string] => [shop(b), s.sold[b], BAKERY_INFO[b].roof]),
          ['left empty-handed', s.walkaways, WALKAWAY_FILL],
        ]
        const label = humanize(segmentPeople(s.segment))
        return (
          <div key={s.segment} className="bar" title={`${label}: ${parts.map(([who, n]) => `${n} ${who}`).join(', ')}`}>
            <span className="bar__label">{label}</span>
            <div className="bar__track bar__track--stacked">
              <div className="bar__stack" style={{ width: `${(s.visits / max) * 100}%` }}>
                {parts.map(([who, n, fill]) =>
                  n > 0 ? (
                    <div key={who} style={{ flexGrow: n, background: fill }}>
                      {n}
                    </div>
                  ) : null,
                )}
              </div>
            </div>
            <span className="bar__value">{s.visits}</span>
          </div>
        )
      })}
    </div>
  )
}

/** Units sold per item, one column per shop, on a shared scale. */
export function ItemBars({ report }: { report: DayReport }) {
  const max = Math.max(1, ...ORDER.flatMap((b) => report.bakeries[b].items.map((i) => i.sold)))
  return (
    <div className="report-cards">
      {ORDER.map((b) => (
        <BarList
          key={b}
          title={shop(b)}
          max={max}
          bars={report.bakeries[b].items.map((item) => ({
            key: item.id,
            label: item.name,
            value: item.sold,
            fill: BAKERY_INFO[b].roof,
            text: String(item.sold),
          }))}
        />
      ))}
    </div>
  )
}

/** Profit per item (sales minus ingredients), most profitable first, on a shared scale. */
export function ItemProfitBars({ report }: { report: DayReport }) {
  const max = Math.max(1, ...ORDER.flatMap((b) => report.bakeries[b].items.map((i) => i.profit ?? 0)))
  return (
    <div className="report-cards">
      {ORDER.map((b) => (
        <BarList
          key={b}
          title={shop(b)}
          max={max}
          bars={[...report.bakeries[b].items]
            .sort((x, y) => (y.profit ?? -Infinity) - (x.profit ?? -Infinity))
            .map((item) => ({
              key: item.id,
              label: item.name,
              value: item.profit ?? 0,
              fill: BAKERY_INFO[b].roof,
              text: item.profit === null ? 'no recipe' : formatMoney(item.profit),
            }))}
        />
      ))}
    </div>
  )
}

/** Each shop's costliest ingredients in dollars, on a shared scale. */
export function IngredientBars({ report, limit = 6 }: { report: DayReport; limit?: number }) {
  const max = Math.max(...ORDER.flatMap((b) => report.bakeries[b].ingredients.map((i) => i.cost)))
  return (
    <div className="report-cards">
      {ORDER.map((b) => (
        <BarList
          key={b}
          title={shop(b)}
          max={max}
          bars={report.bakeries[b].ingredients.slice(0, limit).map((ing) => ({
            key: ing.name,
            label: ing.name,
            value: ing.cost,
            fill: BAKERY_INFO[b].roof,
            text: formatMoney(ing.cost),
          }))}
        />
      ))}
    </div>
  )
}
