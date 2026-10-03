import type { CSSProperties } from 'react'
import { BAKERY_INFO, formatPercent } from './data'
import { Rule } from './Sketch'
import type { BakeryMetrics } from './playback'
import type { Bakery } from './types'

interface Props {
  title: string
  side: 'left' | 'right'
  fill: string
  metrics: BakeryMetrics
  rival: BakeryMetrics
}

const money = (n: number) => `${n < 0 ? '−' : ''}$${Math.abs(n).toFixed(2)}`

/** A bakery's running totals, with a star where it's ahead of the rival. */
export function MetricsPanel({ title, side, fill, metrics, rival }: Props) {
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
    <section
      className={`sketch metrics metrics--${side}`}
      style={{ '--fill': fill } as CSSProperties}
      aria-label={`${title} metrics`}
    >
      <h2 className="metrics__title">{title}</h2>
      <Rule />
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


interface LeadBarProps {
  order: Bakery[] // left to right
  metrics: Record<Bakery, BakeryMetrics>
}

/** Tug of war: each shop's share of the profit so far (sales without a ledger). */
export function LeadBar({ order, metrics }: LeadBarProps) {
  const value = (b: Bakery) => Math.max(0, metrics[b].profit ?? metrics[b].revenue)
  const total = order.reduce((sum, b) => sum + value(b), 0)
  const label = order.every((b) => metrics[b].profit !== null) ? 'Profit so far' : 'Sales so far'
  return (
    <div className="lead">
      <span className="lead__label">{label}</span>
      <div className="report-share" aria-label={label}>
        {order.map((b) => {
          const share = total > 0 ? value(b) / total : 1 / order.length
          return (
            <div key={b} style={{ flexGrow: Math.max(share, 0.12), background: BAKERY_INFO[b].roof }}>
              {formatPercent(share)}
            </div>
          )
        })}
      </div>
    </div>
  )
}
