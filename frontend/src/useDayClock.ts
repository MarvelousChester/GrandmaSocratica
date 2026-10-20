import { useCallback, useEffect, useRef, useState } from 'react'
import { dayEnd, SPEED_MIN_PER_SEC } from './playback'
import type { DayResult } from './types'

/** Dev aid: `?speed=60` plays an hour a second at "1×". */
function baseSpeed(): number {
  const fromUrl = Number(new URLSearchParams(window.location.search).get('speed'))
  return fromUrl > 0 ? fromUrl : SPEED_MIN_PER_SEC
}

/**
 * The simulated minute right now, advancing from opening time in real time
 * until the day ends. Mount it fresh (e.g. with a `key`) for each new day.
 *
 * Returns:
 *  minute, finished, pause controls, `seek` for scrubbing the day, and `skip`.
 */
export function useDayClock(day: DayResult) {
  const [minute, setMinute] = useState(day.config.clock.open_minute)
  const [finished, setFinished] = useState(false)
  const [paused, setPaused] = useState(false)
  const minuteRef = useRef(minute)
  const end = dayEnd(day)

  useEffect(() => {
    if (paused || finished) return
    const rate = baseSpeed()
    let last = performance.now()
    let frame = 0

    // Advance from the last frame so seeking within the day doesn't reset the clock.
    const tick = (now: number) => {
      const m = Math.min(end, minuteRef.current + ((now - last) / 1000) * rate)
      last = now
      minuteRef.current = m
      setMinute(m)
      if (m >= end) setFinished(true)
      else frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [end, finished, paused])

  const seek = useCallback((next: number) => {
    const m = Math.max(day.config.clock.open_minute, Math.min(end, next))
    minuteRef.current = m
    setMinute(m)
    setFinished(m >= end)
  }, [day.config.clock.open_minute, end])

  // The loop sees the minute at `end` on its next frame and finishes.
  const skip = useCallback(() => {
    minuteRef.current = end
    setMinute(end)
    setFinished(true)
    setPaused(false)
  }, [end])

  const togglePause = useCallback(() => setPaused((current) => !current), [])

  return { minute, finished, paused, seek, skip, togglePause }
}
