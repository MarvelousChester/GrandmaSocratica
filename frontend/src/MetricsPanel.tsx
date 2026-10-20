import type { CSSProperties } from 'react'
import { BAKERY_INFO, formatMoney, shop } from './data'
import { Rule } from './Sketch'
import type { BakeryMetrics } from './playback'
import type { Bakery } from './types'

interface Props {
  title: string
  side: 'left' | 'right'
  fill: string
  winnerColor: string
  metrics: BakeryMetrics
  rival: BakeryMetrics
}

const money = (n: number) => `${n < 0 ? '−' : ''}$${Math.abs(n).toFixed(2)}`

/** A bakery's running totals, outlined when it leads the day. */
export function MetricsPanel({ title, side, fill, winnerColor, metrics, rival }: Props) {
  const lead = metrics.profit !== null && rival.profit !== null
    ? metrics.profit - rival.profit
    : metrics.revenue - rival.revenue
  const isWinner = lead > 0
  const rows: { label: string; value: string }[] = [
    { label: 'Revenue', value: money(metrics.revenue) },
    {
      label: 'Profit',
      value: metrics.profit === null ? '—' : money(metrics.profit),
    },
    { label: 'Items sold', value: String(metrics.sold) },
  ]
  return (
    <section
      className={`sketch metrics metrics--${side}${isWinner ? ' metrics--winner' : ''}`}
      style={{ '--fill': fill, '--winner-color': winnerColor } as CSSProperties}
      aria-label={`${title} metrics`}
    >
      <h2 className="metrics__title">{title}</h2>
      <Rule />
      {rows.map((row) => (
        <div key={row.label}>
          <div className="metric">
            <span className="metric__label">{row.label}</span>
            <span className="metric__value">{row.value}</span>
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
  showProfit: boolean
}

/** Side-by-side comparisons of profit and revenue accumulated during the day. */
export function LeadBar({ order, metrics, showProfit }: LeadBarProps) {
  const rows = [
    ...(showProfit ? [{ label: 'PROFIT', value: (b: Bakery) => Math.max(0, metrics[b].profit ?? metrics[b].revenue) }] : []),
    { label: 'REVENUE', value: (b: Bakery) => Math.max(0, metrics[b].revenue) },
  ]
  return (
    <div className="lead">
      {rows.map(({ label, value }) => {
        const values = order.map(value)
        const total = values.reduce((sum, n) => sum + n, 0)
        return (
          <div className="lead__row" key={label}>
            <span className="lead__label">{label}</span>
            <div
              className="lead__bar"
              role="img"
              aria-label={`${label} so far — ${order.map((b) => `${shop(b)}: ${formatMoney(value(b))}`).join(', ')}`}
            >
              {order.map((bakery, index) => (
                <div
                  key={bakery}
                  title={`${shop(bakery)}: ${formatMoney(values[index])}`}
                  style={{
                    flexGrow: total > 0 ? values[index] : 1,
                    background: BAKERY_INFO[bakery].roof,
                  }}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
