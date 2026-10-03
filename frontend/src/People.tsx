import { useEffect, useState } from 'react'
import { hash, leaveAfter, personAt, VIEW_H, VIEW_W, WALK } from './playback'
import type { DayResult } from './types'

const GROUND_Y = 1040 // top of the sidewalk, in Scene viewBox units
const MARGIN = 60 // start this far past the visible edge
const HEIGHT = 230 // of a person, in Scene viewBox units

// Drawn facing right; every PNG in the folder joins the crowd.
const SPRITES = Object.values(
  import.meta.glob<string>('./assets/people/*.png', { eager: true, import: 'default' }),
)

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

/** Every customer on the street at `minute`, each as one of the drawn people. Render inside <Scene>. */
export function People({ day, minute }: { day: DayResult; minute: number }) {
  const edges = useEdges()
  return (
    <>
      {day.events.map((event, i) => {
        if (minute < event.minute - WALK || minute > event.minute + leaveAfter(event)) return null
        const pose = personAt(event, minute, edges)
        if (!pose) return null
        const h = HEIGHT * (0.9 + hash(event.customer_id + 's') * 0.2)
        const sprite = SPRITES[Math.floor(hash(event.customer_id + 'p') * SPRITES.length)]
        return (
          <image
            key={`${event.customer_id}-${i}`}
            href={sprite}
            x={pose.x - h / 2}
            y={GROUND_Y - h}
            width={h}
            height={h}
            preserveAspectRatio="xMidYMax meet"
            opacity={pose.opacity}
            transform={pose.facing === -1 ? `translate(${2 * pose.x} 0) scale(-1 1)` : undefined}
          />
        )
      })}
    </>
  )
}
