import { Rule } from './Sketch'
import type { BakeryMetrics } from './playback'

interface Props {
  title: string
  side: 'left' | 'right'
  metrics: BakeryMetrics
  rival: BakeryMetrics
}

const money = (n: number) => `${n < 0 ? '−' : ''}$${Math.abs(n).toFixed(2)}`

/** A bakery's running totals, with a star where it's ahead of the rival. */
export function MetricsPanel({ title, side, metrics, rival }: Props) {
  const rows: { label: string; value: string; ahead: boolean }[] = [
    { label: 'Revenue', value: money(metrics.revenue), ahead: metrics.revenue > rival.revenue },
    {
      label: 'Profit',
      value: metrics.profit === null ? '—' : money(metrics.profit),
      ahead: metrics.profit !== null && rival.profit !== null && metrics.profit > rival.profit,
    },
    { label: 'Items sold', value: String(metrics.sold), ahead: metrics.sold > rival.sold },
  ]
  return (
    <section className={`sketch metrics metrics--${side}`} aria-label={`${title} metrics`}>
      <h2 className="metrics__title">{title}</h2>
      {rows.map((row) => (
        <div key={row.label}>
          <div className="metric">
            <span className="metric__label">{row.label}</span>
            <span className="metric__value">
              {row.ahead && <span className="metric__star" aria-label="ahead">★</span>}
              {row.value}
            </span>
          </div>
          <Rule />
        </div>
      ))}
    </section>
  )
}
