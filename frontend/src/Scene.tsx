import type { ReactNode } from 'react'
import bakeryArt from './assets/shops/the_bakery.png'
import grandmasArt from './assets/shops/grandmas_bakeria.png'
import { DOOR_X, GROUND_Y } from './playback'
import type { Bakery } from './types'

const SKY = '#b0d6fb'
const SIDEWALK = '#f8d9ae'

// The background rects overshoot the viewBox by this much so they fill any screen shape.
const BLEED = 4000

interface ShopArt {
  src: string
  width: number // in viewBox units
  aspect: number // height / width of the image
  doorX: number // door centre, as a fraction of the width
  footY: number // bottom of the building (not the plants), as a fraction of the height
}

const SHOPS: Record<Bakery, ShopArt> = {
  the_bakery: { src: bakeryArt, width: 420, aspect: 1290 / 1100, doorX: 0.521, footY: 0.923 },
  grandmas_bakeria: { src: grandmasArt, width: 470, aspect: 889 / 1100, doorX: 0.532, footY: 0.92 },
}

/** A shop drawing, placed so its door is at DOOR_X and the building stands on the sidewalk. */
function Shop({ bakery }: { bakery: Bakery }) {
  const { src, width, aspect, doorX, footY } = SHOPS[bakery]
  const height = width * aspect
  return (
    <image
      className={`shop-art shop-art--${bakery}`}
      data-bakery={bakery}
      href={src}
      x={DOOR_X[bakery] - doorX * width}
      y={GROUND_Y - footY * height}
      width={width}
      height={height}
    />
  )
}


/** The street. `children` are drawn in its viewBox coordinates, on the sidewalk in front of the shops. */
export function Scene({ children, landing = false }: { children?: ReactNode; landing?: boolean }) {
  return (
    <div className={`scene${landing ? ' scene--landing' : ''}`} style={{ position: 'absolute', inset: 0, background: SKY, overflow: 'hidden' }}>
      <svg
        viewBox="0 0 1700 1288"
        preserveAspectRatio="xMidYMax meet"
        style={{ display: 'block', width: '100%', height: '100%' }}
        role="img"
        aria-label="Two bakeries side by side on a street"
      >
        <rect x={-BLEED} y={-BLEED} width={1700 + 2 * BLEED} height={1122 + BLEED} fill={SKY} />
        <rect x={-BLEED} y={1122} width={1700 + 2 * BLEED} height={BLEED} fill={SIDEWALK} />

        <g transform="translate(-260 250)" aria-hidden="true">
          <g className="cloud cloud--one" fill="#fff" opacity="0.2">
            <path d="M18 75 C4 73 0 57 9 46 C16 37 29 37 39 43 C42 24 58 12 77 13 C96 13 109 26 112 43 C126 32 147 36 154 51 C172 45 191 53 193 68 C195 82 184 91 168 91 H27 C23 91 19 86 18 75Z" />
          </g>
        </g>
        <g transform="translate(-900 455)" aria-hidden="true">
          <g className="cloud cloud--two" fill="#fff" opacity="0.16">
            <path d="M18 75 C4 73 0 57 9 46 C16 37 29 37 39 43 C42 24 58 12 77 13 C96 13 109 26 112 43 C126 32 147 36 154 51 C172 45 191 53 193 68 C195 82 184 91 168 91 H27 C23 91 19 86 18 75Z" />
          </g>
        </g>

        <Shop bakery="the_bakery" />
        <Shop bakery="grandmas_bakeria" />

        {children}

      </svg>
    </div>
  )
}
