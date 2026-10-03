import { useMemo, useState } from 'react'
import { SegmentedControl } from '@mantine/core'
import { useLocalStorage } from '@mantine/hooks'
import { BAKERY_INFO, CLOCK, formatTime, MENUS, newItemId, PANEL_ORDER } from './data'
import { DayReport, type ReportView } from './DayReport'
import { ItemModal, type ModalTarget } from './ItemModal'
import { MenuPanel } from './MenuPanel'
import { buildReport } from './report'
import { Scene } from './Scene'
import { SketchDefs } from './Sketch'
import type { MenuItem } from './types'
import { useSimulation } from './useSimulation'

type Simulation = ReturnType<typeof useSimulation>

/** One-line outcome of the last Start press: working, failed, or what the day looked like. */
function statusText({ status, day, error }: Simulation): string | null {
  if (status === 'loading') return 'Simulating the day…'
  if (status === 'error') return error
  if (status === 'done' && day) {
    const { events, summary } = day
    if (events.length === 0) return 'No customers came today.'
    const span = `${formatTime(events[0].minute)} – ${formatTime(events[events.length - 1].minute)}`
    return `${summary.visits} visits · ${summary.purchases} sold\n${span}`
  }
  return null
}

export default function App() {
  const [menus, setMenus] = useState(MENUS)
  const sim = useSimulation()
  const loading = sim.status === 'loading'
  const status = statusText(sim)
  const [modal, setModal] = useState<{ opened: boolean; target: ModalTarget | null }>({
    opened: false,
    target: null,
  })
  const [view, setView] = useLocalStorage<ReportView>({ key: 'report-view', defaultValue: 'grandma' })
  const [reportOpen, setReportOpen] = useState(false)
  const report = useMemo(() => (sim.day ? buildReport(sim.day) : null), [sim.day])

  const startDay = async () => {
    const day = await sim.start(PANEL_ORDER.map((bakery) => ({ bakery, items: menus[bakery] })))
    if (day) setReportOpen(true)
  }

  const removeItem = (item: MenuItem) =>
    setMenus((m) => ({ ...m, [item.bakery]: m[item.bakery].filter((i) => i.id !== item.id) }))

  // Replaces an existing item, or appends it to its bakery's menu if it's new.
  const saveItem = (item: MenuItem) => {
    setMenus((m) => {
      const list = m[item.bakery]
      if (list.some((i) => i.id === item.id)) {
        return { ...m, [item.bakery]: list.map((i) => (i.id === item.id ? item : i)) }
      }
      const taken = new Set(Object.values(m).flatMap((items) => items.map((i) => i.id)))
      return { ...m, [item.bakery]: [...list, { ...item, id: newItemId(item.name, taken) }] }
    })
    closeModal()
  }

  const openModal = (target: ModalTarget) => setModal({ opened: true, target })
  // Keep the target while the close animation plays so the title doesn't flicker.
  const closeModal = () => setModal((m) => ({ ...m, opened: false }))

  return (
    <div className="app">
      <SketchDefs />
      <Scene />
      <div className="overlay">
        {PANEL_ORDER.map((bakery, i) => (
          <MenuPanel
            key={bakery}
            title={`${BAKERY_INFO[bakery].name} Menu`}
            side={i === 0 ? 'left' : 'right'}
            fill={BAKERY_INFO[bakery].wall}
            items={menus[bakery]}
            onAdd={() => openModal({ kind: 'add', bakery })}
            onEdit={(item) => openModal({ kind: 'edit', item })}
            onRemove={removeItem}
          />
        ))}
        <div className="center">
          <div className="clock">{formatTime(CLOCK.open_minute)}</div>
          <button
            type="button"
            className="sketch start"
            disabled={loading}
            onClick={startDay}
          >
            {loading ? 'Starting…' : 'Start'}
          </button>
          <div className="status" role="status" data-error={sim.status === 'error' || undefined}>
            {status}
          </div>
          {report && (
            <button type="button" className="sketch report-btn" onClick={() => setReportOpen(true)}>
              {view === 'grandma' ? 'How did it go?' : 'Day report'}
            </button>
          )}
          <SegmentedControl
            className="view-toggle"
            value={view}
            onChange={(v) => setView(v as ReportView)}
            data={[
              { value: 'grandma', label: 'Grandma' },
              { value: 'detailed', label: 'Detailed' },
            ]}
          />
        </div>
      </div>
      <ItemModal opened={modal.opened} target={modal.target} onClose={closeModal} onSave={saveItem} />
      <DayReport opened={reportOpen} report={report} view={view} onClose={() => setReportOpen(false)} />
    </div>
  )
}
