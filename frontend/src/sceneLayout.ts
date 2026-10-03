// Where things sit on the street, in the Scene SVG's viewBox units.
import grandmasShop from './shop-grandmas.webp'
import theBakeryShop from './shop-the-bakery.webp'
import type { Bakery } from './types'

// The shop drawings, cropped to their content. `doorX` is the door's centre and
// `baseY` the bottom of the wall, as fractions of the image; the rest (bushes,
// vines) hangs over the sidewalk.
export const SHOPS: Record<Bakery, { src: string; aspect: number; doorX: number; baseY: number; x: number; width: number }> = {
  the_bakery: { src: theBakeryShop, aspect: 1172 / 1000, doorX: 0.513, baseY: 0.95, x: 330, width: 530 },
  grandmas_bakeria: { src: grandmasShop, aspect: 808 / 1000, doorX: 0.514, baseY: 0.94, x: 890, width: 540 },
}

export const GROUND_Y = 1042 // top of the sidewalk

/** Where customers walk to: each shop's door, in viewBox x. */
export const DOOR_X = Object.fromEntries(
  Object.entries(SHOPS).map(([bakery, s]) => [bakery, s.x + s.doorX * s.width]),
) as Record<Bakery, number>
