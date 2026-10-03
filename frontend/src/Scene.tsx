import type { ReactNode } from 'react'
import { BAKERY_INFO } from './data'
import { GROUND_Y, SHOPS } from './sceneLayout'
import type { Bakery } from './types'

const SKY = '#b0d6fb'
const SIDEWALK = '#f8d9ae'
const ROAD = '#1f1f1f'

// The background rects overshoot the viewBox by this much so they fill any screen shape.
const BLEED = 4000

function Shop({ bakery }: { bakery: Bakery }) {
  const { src, aspect, baseY, x, width } = SHOPS[bakery]
  const height = width * aspect
  return (
    <image
      data-bakery={bakery}
      href={src}
      x={x}
      y={GROUND_Y - baseY * height}
      width={width}
      height={height}
      aria-label={BAKERY_INFO[bakery].label}
    />
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
          {/* Small displacement so outlines wobble like they were drawn by hand (used by People). */}
          <filter id="rough" filterUnits="userSpaceOnUse" x={0} y={0} width={1700} height={1288}>
            <feTurbulence type="fractalNoise" baseFrequency={0.02} numOctaves={2} seed={3} />
            <feDisplacementMap in="SourceGraphic" scale={5} />
          </filter>
        </defs>

        <rect x={-BLEED} y={-BLEED} width={1700 + 2 * BLEED} height={GROUND_Y + BLEED} fill={SKY} />
        <rect x={-BLEED} y={GROUND_Y} width={1700 + 2 * BLEED} height={BLEED} fill={SIDEWALK} />

        <Shop bakery="the_bakery" />
        <Shop bakery="grandmas_bakeria" />

        {children}

        <rect x={-BLEED} y={1123} width={1700 + 2 * BLEED} height={BLEED} fill={ROAD} />
      </svg>
    </div>
  )
}
