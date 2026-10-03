import { Modal, Table, Tabs, Text } from '@mantine/core'
import { formatMoney, formatPercent, humanize, REPORT_ORDER as ORDER, shop } from './data'
import type { DayReport as Report } from './report'
import {
  CrowdBars,
  HourlyChart,
  IngredientBars,
  ItemBars,
  ItemHeatmap,
  ItemProfitBars,
  Legend,
  MoneyBars,
  ShareBar,
} from './ReportCharts'
import type { Bakery } from './types'

export type ReportView = 'grandma' | 'detailed'

/** The day at a glance, in pictures: share, takings, the day's rhythm, the crowd and the shelves. */
function GrandmaView({ report }: { report: Report }) {
  return (
    <div className="report report--grandma">
      <ShareBar report={report} />
      <h4>Money</h4>
      <MoneyBars report={report} />
      <h4>Through the day</h4>
      <HourlyChart report={report} markPeak />
      <Legend walkaways />
      <h4>Who came by</h4>
      <CrowdBars report={report} />
      <Legend walkaways />
      <h4>What sold</h4>
      <ItemBars report={report} />
      {report.bakeries.grandmas_bakeria.ingredients.length > 0 && (
        <>
          <h4>Biggest ingredient costs</h4>
          <IngredientBars report={report} />
        </>
      )}
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
        <Tabs.Tab value="timing">When it sold</Tabs.Tab>
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
        <HourlyChart report={report} />
        <Legend walkaways />
      </Tabs.Panel>

      <Tabs.Panel value="items" pt="md">
        <h4>Profit per item</h4>
        <ItemProfitBars report={report} />
        <Table className="report-table" mt="md">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Item</Table.Th>
              <Table.Th>Bakery</Table.Th>
              <Table.Th>Price</Table.Th>
              <Table.Th>Sold</Table.Th>
              <Table.Th>Revenue</Table.Th>
              <Table.Th>Ingredients</Table.Th>
              <Table.Th>Profit</Table.Th>
              <Table.Th>Margin</Table.Th>
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
                <Table.Td>{fmtOrDash(i.cost)}</Table.Td>
                <Table.Td>{fmtOrDash(i.profit)}</Table.Td>
                <Table.Td>{i.profit === null || i.revenue === 0 ? '–' : formatPercent(i.profit / i.revenue)}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Tabs.Panel>

      <Tabs.Panel value="timing" pt="md">
        <h4>Units sold per item, by hour</h4>
        <ItemHeatmap report={report} counts />
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
        <IngredientBars report={report} />
        <div className="report-cards" style={{ marginTop: 16 }}>
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
