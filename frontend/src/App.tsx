import { useMemo, useState } from 'react'
import { SegmentedControl } from '@mantine/core'
import { useLocalStorage } from '@mantine/hooks'
import { BAKERY_INFO, CLOCK, formatTime, MENUS, newItemId, PANEL_ORDER } from './data'
import { DayReport, type ReportView } from './DayReport'
import { ItemModal, type ModalTarget } from './ItemModal'
import { MenuPanel } from './MenuPanel'
import { LeadBar, MetricsPanel } from './MetricsPanel'
import { People, SalePops } from './People'
import { metricsAt } from './playback'
import { buildReport } from './report'
import { Scene } from './Scene'
import { SketchDefs } from './Sketch'
import { TitleScreen } from './TitleScreen'
import type { DayResult, MenuItem } from './types'
import { SPEED_STEPS, useDayClock } from './useDayClock'
import { useSimulation } from './useSimulation'

interface DayViewProps {
  day: DayResult
  view: ReportView
  onDone: () => void
}

/** The day being played back: people walking, metrics climbing, clock running, then the day's report. */
function DayView({ day, view, onDone }: DayViewProps) {
  const { minute, finished, multiplier, setSpeed, skip } = useDayClock(day)
  const report = useMemo(() => buildReport(day), [day])
  const metrics = metricsAt(day, minute)
  const [left, right] = PANEL_ORDER
  const { open_minute, close_minute } = day.config.clock
  const progress = Math.min(1, Math.max(0, (minute - open_minute) / (close_minute - open_minute)))
  return (
    <>
      <Scene>
        <People day={day} minute={minute} />
        <SalePops day={day} minute={minute} />
      </Scene>
      <div className="overlay">
        {PANEL_ORDER.map((bakery, i) => (
          <MetricsPanel
            key={bakery}
            title={BAKERY_INFO[bakery].label}
            side={i === 0 ? 'left' : 'right'}
            fill={BAKERY_INFO[bakery].wall}
            metrics={metrics[bakery]}
            rival={metrics[bakery === left ? right : left]}
          />
        ))}
        <div className="center center--day">
          <div className="clock" aria-live="off">
            {formatTime(minute)}
          </div>
          <div className="day-progress" role="progressbar" aria-valuenow={Math.round(progress * 100)}>
            <div style={{ width: `${progress * 100}%` }} />
          </div>
          <div className="speeds" role="group" aria-label="Speed">
            {SPEED_STEPS.map((step) => (
              <button
                key={step}
                type="button"
                className="sketch speed"
                data-active={step === multiplier || undefined}
                onClick={() => setSpeed(step)}
                disabled={finished}
              >
                {step}×
              </button>
            ))}
          </div>
          <button type="button" className="sketch control" onClick={skip} disabled={finished}>
            Skip day
          </button>
          <LeadBar order={PANEL_ORDER} metrics={metrics} />
        </div>
      </div>
      <DayReport opened={finished} report={report} view={view} onClose={onDone} closeLabel="Back to menus" />
    </>
  )
}

export default function App() {
  const [begun, setBegun] = useState(false)
  const [menus, setMenus] = useState(MENUS)
  const sim = useSimulation()
  const loading = sim.status === 'loading'
  // Set once Start succeeds; cleared from the YAY modal to go back to editing.
  const [playing, setPlaying] = useState<DayResult | null>(null)
  const [modal, setModal] = useState<{ opened: boolean; target: ModalTarget | null }>({
    opened: false,
    target: null,
  })
  const [view, setView] = useLocalStorage<ReportView>({ key: 'report-view', defaultValue: 'grandma' })
  const [reportOpen, setReportOpen] = useState(false)
  const report = useMemo(() => (sim.day ? buildReport(sim.day) : null), [sim.day])

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

  const start = async () => {
    const day = await sim.start(PANEL_ORDER.map((bakery) => ({ bakery, items: menus[bakery] })))
    if (day) setPlaying(day)
  }

  if (!begun) {
    return (
      <div className="app">
        <SketchDefs />
        <Scene />
        <TitleScreen onBegin={() => setBegun(true)} />
      </div>
    )
  }

  if (playing) {
    return (
      <div className="app">
        <SketchDefs />
        <DayView key={playing.config.seed} day={playing} view={view} onDone={() => setPlaying(null)} />
      </div>
    )
  }

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
        <div className="center center--setup">
          <div className="clock">{formatTime(CLOCK.open_minute)}</div>
          <button
            type="button"
            className="sketch start"
            disabled={loading}
            onClick={start}
          >
            {loading ? 'Starting…' : 'Start'}
          </button>
          <div className="status" role="status" data-error={sim.status === 'error' || undefined}>
            {loading ? 'Simulating the day…' : sim.status === 'error' ? sim.error : null}
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
