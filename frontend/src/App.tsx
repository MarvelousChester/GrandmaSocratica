import { useState } from 'react'
import { BAKERY_INFO, CLOCK, formatTime, MENUS, newItemId, PANEL_ORDER } from './data'
import { DoneModal } from './DoneModal'
import { ItemModal, type ModalTarget } from './ItemModal'
import { MenuPanel } from './MenuPanel'
import { MetricsPanel } from './MetricsPanel'
import { People } from './People'
import { metricsAt } from './playback'
import { Scene } from './Scene'
import { SketchDefs } from './Sketch'
import type { DayResult, MenuItem } from './types'
import { useDayClock } from './useDayClock'
import { useSimulation } from './useSimulation'

/** The day being played back: people walking, metrics climbing, clock running. */
function DayView({ day, onDone }: { day: DayResult; onDone: () => void }) {
  const { minute, finished, multiplier, cycleSpeed, skip } = useDayClock(day)
  const metrics = metricsAt(day, minute)
  const [left, right] = PANEL_ORDER
  return (
    <>
      <Scene>
        <People day={day} minute={minute} />
      </Scene>
      <div className="overlay">
        {PANEL_ORDER.map((bakery, i) => (
          <MetricsPanel
            key={bakery}
            title={BAKERY_INFO[bakery].label}
            side={i === 0 ? 'left' : 'right'}
            metrics={metrics[bakery]}
            rival={metrics[bakery === left ? right : left]}
          />
        ))}
        <div className="center">
          <div className="clock" aria-live="off">
            {formatTime(minute)}
          </div>
          <div className="controls">
            <button
              type="button"
              className="sketch control"
              onClick={cycleSpeed}
              disabled={finished}
              aria-label={`Speed ${multiplier}×, click to change`}
            >
              {multiplier}× speed
            </button>
            <button type="button" className="sketch control" onClick={skip} disabled={finished}>
              Skip day
            </button>
          </div>
        </div>
      </div>
      <DoneModal opened={finished} day={day} onClose={onDone} />
    </>
  )
}

export default function App() {
  const [menus, setMenus] = useState(MENUS)
  const sim = useSimulation()
  const loading = sim.status === 'loading'
  // Set once Start succeeds; cleared from the YAY modal to go back to editing.
  const [playing, setPlaying] = useState<DayResult | null>(null)
  const [modal, setModal] = useState<{ opened: boolean; target: ModalTarget | null }>({
    opened: false,
    target: null,
  })

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

  if (playing) {
    return (
      <div className="app">
        <SketchDefs />
        <DayView key={playing.config.seed} day={playing} onDone={() => setPlaying(null)} />
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
        <div className="center">
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
        </div>
      </div>
      <ItemModal opened={modal.opened} target={modal.target} onClose={closeModal} onSave={saveItem} />
    </div>
  )
}
