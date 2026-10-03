import { useCallback, useRef, useState } from 'react'
import { simulateDay } from './api'
import type { DayResult, Menu } from './types'

export type SimulationStatus = 'idle' | 'loading' | 'done' | 'error'

interface State {
  status: SimulationStatus
  day: DayResult | null // the last successful day, including its full event schedule
  error: string | null
}

/** Runs one simulated day on demand and holds the schedule that comes back. */
export function useSimulation() {
  const [state, setState] = useState<State>({ status: 'idle', day: null, error: null })
  const running = useRef(false)

  const start = useCallback(async (menus: Menu[]) => {
    if (running.current) return
    running.current = true
    setState((s) => ({ ...s, status: 'loading', error: null }))
    try {
      const day = await simulateDay(menus)
      setState({ status: 'done', day, error: null })
    } catch (e) {
      setState((s) => ({ ...s, status: 'error', error: e instanceof Error ? e.message : String(e) }))
    } finally {
      running.current = false
    }
  }, [])

  return { ...state, start }
}
