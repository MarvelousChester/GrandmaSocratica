import type { CSSProperties } from 'react'
import { useState } from 'react'
import { Button, Group, Modal, Select, Table, Tabs, Text, TextInput } from '@mantine/core'
import { BAKERY_INFO, formatMoney, formatPercent, humanize, REPORT_ORDER as ORDER, shop } from './data'
import { verdict, type DayReport as Report } from './report'
import {
  HourlyChart,
  IngredientBars,
  ItemHeatmap,
  ItemProfitBars,
  Legend,
} from './ReportCharts'
import type { Bakery } from './types'

export type ReportView = 'grandma' | 'detailed'

function Verdict({ report }: { report: Report }) {
  const result = verdict(report)
  if (!result.winner) return <p className="report-verdict">Neck and neck with The Bakery!</p>

  const color = BAKERY_INFO[result.winner].roof
  const amount = formatMoney(result.lead)
  return (
    <p className="report-verdict">
      {result.winner === 'grandmas_bakeria' ? (
        <><span style={{ color }}>Grandma's</span> won the day by {amount} in {result.what}!</>
      ) : (
        <><span style={{ color }}>The Bakery</span> beat us by {amount} in {result.what}. Let's tweak the menu!</>
      )}
    </p>
  )
}

/** A quick result and the three numbers that explain it. */
function GrandmaView({ report }: { report: Report }) {
  return (
    <div className="report report--grandma">
      <div className="grandma-scorecard">
        {ORDER.map((bakery) => {
          const result = report.bakeries[bakery]
          return (
            <section
              key={bakery}
              className="grandma-scorecard__bakery"
              style={{ '--bakery-color': BAKERY_INFO[bakery].roof } as CSSProperties}
            >
              <h4>{shop(bakery)}</h4>
              <dl>
                <div>
                  <dt>Orders</dt>
                  <dd>{result.sold}</dd>
                </div>
                <div>
                  <dt>Sales</dt>
                  <dd>{formatMoney(result.revenue)}</dd>
                </div>
                <div>
                  <dt>Profit</dt>
                  <dd>{fmtOrDash(result.profit)}</dd>
                </div>
              </dl>
            </section>
          )
        })}
      </div>
    </div>
  )
}

/** Every figure the day produced, in tables. */
function DetailedView({ report }: { report: Report }) {
  const [itemSearch, setItemSearch] = useState('')
  const [itemBakery, setItemBakery] = useState<'all' | Bakery>('all')
  const [activeTab, setActiveTab] = useState<string | null>('money')
  const query = itemSearch.trim().toLowerCase()
  const filterItems = (bakery: Bakery) =>
    itemBakery !== 'all' && itemBakery !== bakery
      ? []
      : report.bakeries[bakery].items.filter((item) => item.name.toLowerCase().includes(query))
  const itemReport: Report = {
    ...report,
    bakeries: {
      ...report.bakeries,
      grandmas_bakeria: { ...report.bakeries.grandmas_bakeria, items: filterItems('grandmas_bakeria') },
      the_bakery: { ...report.bakeries.the_bakery, items: filterItems('the_bakery') },
    },
  }
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
  const items = ORDER.flatMap((b) => itemReport.bakeries[b].items)

  return (
    <Tabs value={activeTab} onChange={setActiveTab} className="report">
      <Tabs.List>
        <Tabs.Tab value="money">Money</Tabs.Tab>
        <Tabs.Tab value="items">Items</Tabs.Tab>
        <Tabs.Tab value="timing">When it sold</Tabs.Tab>
        <Tabs.Tab value="customers">Customers</Tabs.Tab>
        <Tabs.Tab value="ingredients">Ingredients</Tabs.Tab>
      </Tabs.List>

      {(activeTab === 'items' || activeTab === 'timing') && (
        <Group className="grandchild-filters" grow>
          <TextInput
            label="Search items"
            placeholder="Type an item name"
            value={itemSearch}
            onChange={(event) => setItemSearch(event.currentTarget.value)}
          />
          <Select
            label="Bakery"
            value={itemBakery}
            onChange={(value) => value && setItemBakery(value as 'all' | Bakery)}
            data={[
              { value: 'all', label: 'All bakeries' },
              { value: 'grandmas_bakeria', label: "Grandma's Bakeria" },
              { value: 'the_bakery', label: 'The Bakery' },
            ]}
            allowDeselect={false}
          />
        </Group>
      )}

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
        <ItemProfitBars report={itemReport} />
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
        {items.length === 0 && <Text c="dimmed" mt="sm">No items match those filters.</Text>}
      </Tabs.Panel>

      <Tabs.Panel value="timing" pt="md">
        <h4>Units sold per item, by hour</h4>
        <ItemHeatmap report={itemReport} />
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

    </Tabs>
  )
}

const fmtOrDash = (dollars: number | null) => (dollars === null ? '–' : formatMoney(dollars))

interface Props {
  opened: boolean
  report: Report | null
  view: ReportView
  onClose: () => void
  closeLabel?: string // shows a button at the bottom that closes the report
}

export function DayReport({ opened, report, view, onClose, closeLabel }: Props) {
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
      {report && (
        <>
          <Verdict report={report} />
          {view === 'grandma' ? <GrandmaView report={report} /> : <DetailedView report={report} />}
        </>
      )}
      {closeLabel && (
        <Group justify="flex-end" mt="lg">
          <Button className="sk-btn sk-btn--primary" onClick={onClose}>
            {closeLabel}
          </Button>
        </Group>
      )}
    </Modal>
  )
}
