import { useCallback, useEffect, useRef, useState } from 'react'
import { dayEnd, SPEED_MIN_PER_SEC } from './playback'
import type { DayResult } from './types'

/** The speed button steps through these, then wraps back to normal. */
export const SPEED_STEPS = [1, 2, 5, 10]

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
 *  minute, finished, the current speed multiplier, `cycleSpeed` (1× -> 2× -> 5× -> 10× -> 1×)
 *  and `skip`, which jumps straight to the end of the day.
 */
export function useDayClock(day: DayResult) {
  const [minute, setMinute] = useState(day.config.clock.open_minute)
  const [finished, setFinished] = useState(false)
  const [multiplier, setMultiplier] = useState(SPEED_STEPS[0])
  // Read by the animation loop, so a speed change applies from the next frame on.
  const multiplierRef = useRef(multiplier)
  const minuteRef = useRef(minute)
  const end = dayEnd(day)

  useEffect(() => {
    const rate = baseSpeed()
    let last = performance.now()
    let frame = 0

    // Advance by elapsed time at whatever speed is set now, so changing speed
    // mid-day doesn't jump the clock.
    const tick = (now: number) => {
      const m = Math.min(end, minuteRef.current + ((now - last) / 1000) * rate * multiplierRef.current)
      last = now
      minuteRef.current = m
      setMinute(m)
      if (m >= end) setFinished(true)
      else frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [end])

  const cycleSpeed = useCallback(() => {
    const next = SPEED_STEPS[(SPEED_STEPS.indexOf(multiplierRef.current) + 1) % SPEED_STEPS.length]
    multiplierRef.current = next
    setMultiplier(next)
  }, [])

  // The loop sees the minute at `end` on its next frame and finishes.
  const skip = useCallback(() => {
    minuteRef.current = end
  }, [end])

  return { minute, finished, multiplier, cycleSpeed, skip }
}
