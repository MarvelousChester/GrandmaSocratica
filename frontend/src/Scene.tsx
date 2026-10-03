import type { ReactNode } from 'react'
import { BAKERY_INFO } from './data'
import type { Bakery } from './types'

const INK = '#1e1e1e'
const SKY = '#b0d6fb'
const SIDEWALK = '#f8d9ae'
const ROAD = '#1f1f1f'

// The background rects overshoot the viewBox by this much so they fill any screen shape.
const BLEED = 4000

// Scalloped awning roof, hand-tuned so the bumps are a little uneven.
const ROOF_PATH = `
  M 336 815
  C 360 790, 405 750, 427 715
  C 520 708, 690 695, 765 697
  C 805 730, 840 770, 865 822
  L 868 826
  L 838 828
  C 822 826, 814 812, 810 795
  C 800 828, 785 846, 760 846
  C 730 846, 700 828, 688 808
  C 684 822, 672 834, 650 834
  C 625 834, 608 825, 604 806
  C 600 840, 580 868, 540 872
  C 495 872, 455 840, 445 812
  C 440 835, 425 852, 400 852
  C 375 852, 345 835, 338 817
  Z
`

interface ShopProps {
  bakery: Bakery
  dx?: number
  dy?: number
}

function Shop({ bakery, dx = 0, dy = 0 }: ShopProps) {
  const { roof, wall } = BAKERY_INFO[bakery]
  return (
    <g data-bakery={bakery} transform={`translate(${dx} ${dy})`}>
      <rect x={357} y={815} width={491} height={225} rx={30} fill={wall} />
      <rect x={560} y={900} width={100} height={135} rx={22} fill={INK} />
      <path d={ROOF_PATH} fill={roof} />
    </g>
  )
}

/** The street. `children` are drawn in its viewBox coordinates, on the sidewalk in front of the shops. */
export function Scene({ children }: { children?: ReactNode }) {
  return (
    <div style={{ position: 'absolute', inset: 0, background: SKY, overflow: 'hidden' }}>
      <svg
        viewBox="0 0 1700 1288"
        preserveAspectRatio="xMidYMax meet"
        style={{ display: 'block', width: '100%', height: '100%' }}
        role="img"
        aria-label="Two bakeries side by side on a street"
      >
        <defs>
          {/* Small displacement so every outline wobbles like it was drawn by hand. */}
          <filter id="rough" filterUnits="userSpaceOnUse" x={0} y={0} width={1700} height={1288}>
            <feTurbulence type="fractalNoise" baseFrequency={0.02} numOctaves={2} seed={3} />
            <feDisplacementMap in="SourceGraphic" scale={5} />
          </filter>
        </defs>

        <rect x={-BLEED} y={-BLEED} width={1700 + 2 * BLEED} height={1042 + BLEED} fill={SKY} />
        <rect x={-BLEED} y={1042} width={1700 + 2 * BLEED} height={BLEED} fill={SIDEWALK} />

        <g filter="url(#rough)" stroke={INK} strokeWidth={3.5} strokeLinejoin="round" strokeLinecap="round">
          <Shop bakery="the_bakery" />
          <Shop bakery="grandmas_bakeria" dx={548} dy={-8} />
        </g>

        {children}

        <rect x={-BLEED} y={1123} width={1700 + 2 * BLEED} height={BLEED} fill={ROAD} />
      </svg>
    </div>
  )
}
