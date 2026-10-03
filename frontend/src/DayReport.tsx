import type { CSSProperties } from 'react'
import { Modal, Table, Tabs, Text } from '@mantine/core'
import { BAKERY_INFO, formatHour, formatMoney, formatPercent, humanize, segmentPeople } from './data'
import { busiestHour, hourVisits, pickiestSegment, type DayReport as Report, type HourRow } from './report'
import type { Bakery } from './types'

export type ReportView = 'grandma' | 'detailed'

// Grandma first: she's who the player is rooting for.
const ORDER: Bakery[] = ['grandmas_bakeria', 'the_bakery']
const WALKAWAY_FILL = '#d9d4cf'

const shop = (bakery: Bakery) => BAKERY_INFO[bakery].shop

interface ChartProps {
  hours: HourRow[]
  walkaways: boolean
}

/** Visitors per hour as stacked bars: each bakery's sales, then (optionally) walk-aways. */
function HourlyChart({ hours, walkaways }: ChartProps) {
  const height = 120
  const barWidth = 28
  const gap = 10
  const peak = Math.max(1, ...hours.map((h) => (walkaways ? hourVisits(h) : hourVisits(h) - h.walkaways)))
  const scale = (n: number) => (n / peak) * height

  return (
    <svg
      className="report-chart"
      viewBox={`0 0 ${hours.length * (barWidth + gap)} ${height + 22}`}
      role="img"
      aria-label="Customers per hour"
    >
      {hours.map((h, i) => {
        const parts: [string, number, string][] = [
          ...ORDER.map((b): [string, number, string] => [shop(b), h.sold[b], BAKERY_INFO[b].roof]),
          ...(walkaways ? [['walked away', h.walkaways, WALKAWAY_FILL] as [string, number, string]] : []),
        ]
        let top = height
        const x = i * (barWidth + gap) + gap / 2
        return (
          <g key={h.hour}>
            <title>
              {`${formatHour(h.hour)}: ${parts.map(([label, n]) => `${n} ${label}`).join(', ')}`}
            </title>
            {parts.map(([label, n, fill]) => {
              top -= scale(n)
              return n > 0 ? (
                <rect key={label} x={x} y={top} width={barWidth} height={scale(n)} rx={4} fill={fill} stroke="var(--ink)" strokeWidth={1.5} />
              ) : null
            })}
            <text x={x + barWidth / 2} y={height + 16} textAnchor="middle" fontSize={11}>
              {h.hour % 2 === 0 ? formatHour(h.hour) : ''}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function Legend({ walkaways }: { walkaways: boolean }) {
  const keys: [string, string][] = [
    ...ORDER.map((b): [string, string] => [shop(b), BAKERY_INFO[b].roof]),
    ...(walkaways ? [['Walked away', WALKAWAY_FILL] as [string, string]] : []),
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

function ShareBar({ report }: { report: Report }) {
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

/** Plain-language day: who sold what, money in the till, and what to notice. */
function GrandmaView({ report }: { report: Report }) {
  const busiest = busiestHour(report)
  const pickiest = pickiestSegment(report)
  return (
    <div className="report">
      <ShareBar report={report} />
      <div className="report-cards">
        {ORDER.map((b) => {
          const r = report.bakeries[b]
          const best = r.items[0]
          const unsold = r.items.filter((i) => i.sold === 0)
          return (
            <section key={b} className="sketch sk-box report-card" style={{ '--fill': BAKERY_INFO[b].wall } as CSSProperties}>
              <h3>{shop(b)}</h3>
              <p>
                Sold <b>{r.sold}</b> {r.sold === 1 ? 'treat' : 'treats'}
              </p>
              <p>
                Money in the till: <b>{formatMoney(r.revenue)}</b>
              </p>
              {r.profit !== null && (
                <p>
                  Kept after ingredients: <b>{formatMoney(r.profit)}</b>
                </p>
              )}
              {best && best.sold > 0 && (
                <p>
                  Best seller: <b>{best.name}</b> ({best.sold} sold)
                </p>
              )}
              {unsold.length > 0 && <p>Nobody bought: {unsold.map((i) => i.name).join(', ')}</p>}
            </section>
          )
        })}
      </div>
      <ul className="report-notes">
        {busiest && (
          <li>
            Busiest around <b>{formatHour(busiest.hour)}</b>, with {hourVisits(busiest)} people coming by.
          </li>
        )}
        {report.walkaways > 0 && (
          <li>
            <b>{report.walkaways}</b> of {report.visits} people left without buying anything.
            {pickiest &&
              ` ${humanize(segmentPeople(pickiest.segment))} were the hardest to please (${pickiest.walkaways} of ${pickiest.visits} left).`}
          </li>
        )}
      </ul>
      <h4>Customers through the day</h4>
      <HourlyChart hours={report.hours} walkaways={false} />
      <Legend walkaways={false} />
    </div>
  )
}

/** Every figure the day produced, in tables. */
function DetailedView({ report }: { report: Report }) {
  const rows: [string, (b: Bakery) => string][] = [
    ['Sold', (b) => String(report.bakeries[b].sold)],
    ['Share of sales', (b) => formatPercent(report.bakeries[b].share)],
    ['Revenue', (b) => formatMoney(report.bakeries[b].revenue)],
    ['Ingredient cost', (b) => fmtOrDash(report.bakeries[b].cost)],
    ['Gross profit', (b) => fmtOrDash(report.bakeries[b].profit)],
    [
      'Gross margin',
      (b) => {
        const { profit, revenue } = report.bakeries[b]
        return profit === null || revenue === 0 ? '–' : formatPercent(profit / revenue)
      },
    ],
  ]
  const items = ORDER.flatMap((b) => report.bakeries[b].items)

  return (
    <Tabs defaultValue="money" className="report">
      <Tabs.List>
        <Tabs.Tab value="money">Money</Tabs.Tab>
        <Tabs.Tab value="items">Items</Tabs.Tab>
        <Tabs.Tab value="customers">Customers</Tabs.Tab>
        <Tabs.Tab value="ingredients">Ingredients</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="money" pt="md">
        <Table className="report-table">
          <Table.Thead>
            <Table.Tr>
              <Table.Th />
              {ORDER.map((b) => (
                <Table.Th key={b}>{shop(b)}</Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map(([label, value]) => (
              <Table.Tr key={label}>
                <Table.Td>{label}</Table.Td>
                {ORDER.map((b) => (
                  <Table.Td key={b}>{value(b)}</Table.Td>
                ))}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        <h4>Visits per hour</h4>
        <HourlyChart hours={report.hours} walkaways />
        <Legend walkaways />
      </Tabs.Panel>

      <Tabs.Panel value="items" pt="md">
        <Table className="report-table">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Item</Table.Th>
              <Table.Th>Bakery</Table.Th>
              <Table.Th>Price</Table.Th>
              <Table.Th>Sold</Table.Th>
              <Table.Th>Revenue</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((i) => (
              <Table.Tr key={i.id}>
                <Table.Td>
                  {i.name}
                  {report.uncosted.includes(i.id) && <span className="report-flag"> no recipe</span>}
                </Table.Td>
                <Table.Td>{shop(i.bakery)}</Table.Td>
                <Table.Td>{formatMoney(i.price)}</Table.Td>
                <Table.Td>{i.sold}</Table.Td>
                <Table.Td>{formatMoney(i.revenue)}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Tabs.Panel>

      <Tabs.Panel value="customers" pt="md">
        <Table className="report-table">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Segment</Table.Th>
              <Table.Th>Visits</Table.Th>
              {ORDER.map((b) => (
                <Table.Th key={b}>{shop(b)}</Table.Th>
              ))}
              <Table.Th>Walked away</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {report.segments.map((s) => (
              <Table.Tr key={s.segment}>
                <Table.Td>{humanize(s.segment)}</Table.Td>
                <Table.Td>{s.visits}</Table.Td>
                {ORDER.map((b) => (
                  <Table.Td key={b}>{s.sold[b]}</Table.Td>
                ))}
                <Table.Td>
                  {s.walkaways} ({formatPercent(s.walkaways / s.visits)})
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        <Text size="sm" mt="sm">
          {report.visits} visits, {report.purchases} purchases, {report.walkaways} walked away.
        </Text>
      </Tabs.Panel>

      <Tabs.Panel value="ingredients" pt="md">
        <div className="report-cards">
          {ORDER.map((b) => (
            <div key={b}>
              <h4>{shop(b)}</h4>
              <Table className="report-table">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Ingredient</Table.Th>
                    <Table.Th>Used</Table.Th>
                    <Table.Th>Cost</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {report.bakeries[b].ingredients.slice(0, 8).map((ing) => (
                    <Table.Tr key={ing.name}>
                      <Table.Td>{ing.name}</Table.Td>
                      <Table.Td>{(ing.grams / 1000).toFixed(2)} kg</Table.Td>
                      <Table.Td>{formatMoney(ing.cost)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </div>
          ))}
        </div>
      </Tabs.Panel>

      <Text size="sm" c="dimmed" mt="md">
        Seed {report.seed}
      </Text>
    </Tabs>
  )
}

const fmtOrDash = (dollars: number | null) => (dollars === null ? '–' : formatMoney(dollars))

interface Props {
  opened: boolean
  report: Report | null
  view: ReportView
  onClose: () => void
}

export function DayReport({ opened, report, view, onClose }: Props) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={view === 'grandma' ? 'How did the day go?' : 'Day report'}
      size="xl"
      yOffset="6vh"
      classNames={{
        content: 'sketch sk-modal',
        header: 'sk-modal__header',
        title: 'sk-modal__title',
        close: 'sk-modal__close',
      }}
    >
      {report && (view === 'grandma' ? <GrandmaView report={report} /> : <DetailedView report={report} />)}
    </Modal>
  )
}
