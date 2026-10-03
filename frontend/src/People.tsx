import { useEffect, useState } from 'react'
import { hash, leaveAfter, personAt, VIEW_H, VIEW_W, WALK } from './playback'
import { GROUND_Y } from './sceneLayout'
import type { DayResult } from './types'

const MARGIN = 60 // start this far past the visible edge

/**
 * x just past the visible left and right edges. The Scene SVG is
 * `xMidYMax meet`, so a window wider than the viewBox shows extra street on
 * both sides.
 */
function useEdges() {
  const compute = () => {
    const half = Math.max(VIEW_W / 2, (VIEW_H * window.innerWidth) / window.innerHeight / 2)
    return { left: VIEW_W / 2 - half - MARGIN, right: VIEW_W / 2 + half + MARGIN }
  }
  const [edges, setEdges] = useState(compute)
  useEffect(() => {
    const onResize = () => setEdges(compute())
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  return edges
}

/** Every customer on the street at `minute`, as a black oval. Render inside <Scene>. */
export function People({ day, minute }: { day: DayResult; minute: number }) {
  const edges = useEdges()
  return (
    <g filter="url(#rough)">
      {day.events.map((event, i) => {
        if (minute < event.minute - WALK || minute > event.minute + leaveAfter(event)) return null
        const pose = personAt(event, minute, edges)
        if (!pose) return null
        const scale = 0.9 + hash(event.customer_id + 's') * 0.2
        const ry = 105 * scale
        return (
          <ellipse
            key={`${event.customer_id}-${i}`}
            cx={pose.x}
            cy={GROUND_Y - ry}
            rx={30 * scale}
            ry={ry}
            fill="#1e1e1e"
            opacity={pose.opacity}
          />
        )
      })}
    </g>
  )
}
