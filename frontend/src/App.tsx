import { useMemo, useState } from 'react'
import { SegmentedControl, Slider } from '@mantine/core'
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
import { PauseIcon, PlayIcon, SketchDefs, SkipIcon } from './Sketch'
import { TitleScreen } from './TitleScreen'
import type { DayResult, MenuItem } from './types'
import { SPEED_STEPS, useDayClock } from './useDayClock'
import { useSimulation } from './useSimulation'

interface DayViewProps {
  day: DayResult
  view: ReportView
  onViewChange: (view: ReportView) => void
  onDone: () => void
}

/** The day being played back: people walking, metrics climbing, clock running, then the day's report. */
function DayView({ day, view, onViewChange, onDone }: DayViewProps) {
  const { minute, finished, paused, multiplier, setSpeed, skip, togglePause } = useDayClock(day)
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
      <div className="overlay overlay--day">
        <div className="day-topbar">
          <LeadBar order={PANEL_ORDER} metrics={metrics} showProfit={view === 'detailed'} />
        </div>
        {PANEL_ORDER.map((bakery, i) => (
          <MetricsPanel
            key={bakery}
            title={BAKERY_INFO[bakery].label}
            side={i === 0 ? 'left' : 'right'}
            fill={BAKERY_INFO[bakery].wall}
            winnerColor={BAKERY_INFO[bakery].roof}
            metrics={metrics[bakery]}
            rival={metrics[bakery === left ? right : left]}
          />
        ))}
        <div className="center center--day">
          <div className="day-topbar__time">
            <div className="clock" aria-live="off">
              {formatTime(minute)}
            </div>
            <div className="day-progress" role="progressbar" aria-valuenow={Math.round(progress * 100)}>
              <div style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
          <div className="speed-control">
            <button
              type="button"
              className="playback-icon"
              aria-label={paused ? 'Resume playback' : 'Pause playback'}
              onClick={togglePause}
              disabled={finished}
            >
              {paused ? <PlayIcon /> : <PauseIcon />}
            </button>
            <Slider
              aria-label="Playback speed"
              value={SPEED_STEPS.indexOf(multiplier)}
              onChange={(index) => setSpeed(SPEED_STEPS[index])}
              min={0}
              max={SPEED_STEPS.length - 1}
              step={1}
              marks={[{ value: 0, label: '1×' }, { value: SPEED_STEPS.length - 1, label: '10×' }]}
              aria-valuetext={`${multiplier} times speed`}
              disabled={finished}
              color="#f8c9c9"
              thumbSize={20}
              size={12}
              className="speed-control__slider"
              label={null}
            />
            <button
              type="button"
              className="playback-icon"
              aria-label="Skip to end of day"
              onClick={skip}
              disabled={finished}
            >
              <SkipIcon />
            </button>
          </div>
        </div>
        <SegmentedControl
          className="view-toggle game-view-toggle"
          value={view}
          onChange={(value) => onViewChange(value as ReportView)}
          data={[
            { value: 'grandma', label: 'Grandma' },
            { value: 'detailed', label: 'Grandchild' },
          ]}
        />
      </div>
      <DayReport opened={finished} report={report} view={view} onClose={onDone} closeLabel="Back to menus" />
    </>
  )
}

export default function App() {
  const [begun, setBegun] = useState(false)
  const [housesSettled, setHousesSettled] = useState(false)
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

  if (!begun || !housesSettled) {
    return (
      <div className="app">
        <SketchDefs />
        <Scene landing={!begun} />
        {(!begun || !housesSettled) && (
          <TitleScreen
            leaving={begun}
            onBegin={() => {
              setBegun(true)
              const delay = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1150
              window.setTimeout(() => setHousesSettled(true), delay)
            }}
          />
        )}
      </div>
    )
  }

  if (playing) {
    return (
      <div className="app">
        <SketchDefs />
        <DayView
          key={playing.config.seed}
          day={playing}
          view={view}
          onViewChange={(nextView) => setView(nextView)}
          onDone={() => setPlaying(null)}
        />
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
          <SegmentedControl
            className="view-toggle"
            value={view}
            onChange={(v) => setView(v as ReportView)}
            data={[
              { value: 'grandma', label: 'Grandma' },
              { value: 'detailed', label: 'Grandchild' },
            ]}
          />
          {report && (
            <button type="button" className="sketch report-btn" onClick={() => setReportOpen(true)}>
              {view === 'grandma' ? 'How did it go?' : 'Day report'}
            </button>
          )}
        </div>
      </div>
      <ItemModal opened={modal.opened} target={modal.target} onClose={closeModal} onSave={saveItem} />
      <DayReport opened={reportOpen} report={report} view={view} onClose={() => setReportOpen(false)} />
    </div>
  )
}
