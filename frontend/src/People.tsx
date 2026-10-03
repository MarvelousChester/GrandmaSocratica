import { useEffect, useMemo, useState } from 'react'
import {
  DOOR_X, GROUND_Y, hash, leaveAfter, personAt, popAt, VIEW_H, VIEW_W, WALK,
} from './playback'
import type { DayResult } from './types'

const MARGIN = 60 // start this far past the visible edge
const HEIGHT = 200 // of a person, in Scene viewBox units

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


const POP_Y = 800 // where a sale's "+$" starts, above the door
const POP_RISE = 110
// Three lanes across a shopfront. A "+$00.00" is ~150 units wide at the pop
// font size, and the two doors are only 548 apart, so a lane can sit at most
// ~200 either side of its own door before a sale drifts into the neighbour's.
// Stacking them vertically instead is not an option: there is barely a text's
// height between POP_Y and the metrics panels that would cover them.
const POP_LANE = 150
const POP_LANES = 3

/**
 * Each sale's lane over its own shopfront: consecutive sales at one shop take
 * different lanes, cycling through POP_LANES.
 *
 * Sales cluster, and at 10x several are in the air at once. Drawn at the door
 * they land on top of each other and turn to mush. The lane comes from the
 * sale's position in that shop's run of sales, so it is fixed for the whole
 * life of the pop rather than shifting as neighbours come and go.
 */
function saleLanes(day: DayResult): number[] {
  const seen: Record<string, number> = {}
  return day.events.map((event) => {
    const bakery = event.choice.bakery
    if (!event.choice.purchased || !bakery) return 0
    const n = (seen[bakery] = (seen[bakery] ?? 0) + 1)
    return ((n % POP_LANES) - (POP_LANES - 1) / 2) * POP_LANE
  })
}

/** A "+$price" floating up from the door at each sale. Render inside <Scene>. */
export function SalePops({ day, minute }: { day: DayResult; minute: number }) {
  const lanes = useMemo(() => saleLanes(day), [day])
  return (
    <>
      {day.events.map((event, i) => {
        const t = popAt(event, minute)
        if (t === null || !event.choice.bakery) return null
        return (
          <text
            key={`${event.customer_id}-${i}`}
            className="sale-pop"
            x={DOOR_X[event.choice.bakery] + lanes[i]}
            y={POP_Y - t * POP_RISE}
            opacity={1 - t * t}
          >
            +${event.choice.price.toFixed(2)}
          </text>
        )
      })}
    </>
  )
}
