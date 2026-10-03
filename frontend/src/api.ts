import type { DayResult, Menu, SimulateRequest } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? ''
const UNREACHABLE = "Can't reach the backend. Is it running?"

/** FastAPI sends `{detail: string}`, or `{detail: [{msg, ...}]}` for a 422. */
async function errorMessage(res: Response): Promise<string> {
  // The dev proxy answers 502 itself when nothing is listening.
  const fallback = [502, 503, 504].includes(res.status) ? UNREACHABLE : `Backend error (${res.status})`
  try {
    const { detail } = await res.json()
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') {
      return `Backend rejected the menus: ${detail[0].msg}`
    }
  } catch {
    // Not JSON; use the status.
  }
  return fallback
}

/**
 * Sends both menus to the backend and returns the whole day's simulation.
 * `VITE_USE_MOCK=1` returns the sample day instead (ignores the menus), for UI
 * work without a backend.
 */
export async function simulateDay(menus: Menu[]): Promise<DayResult> {
  if (import.meta.env.VITE_USE_MOCK === '1') {
    await new Promise((resolve) => setTimeout(resolve, 600))
    const sample = await import('../sample_data/day_seed0.json')
    return sample.default as unknown as DayResult
  }

  const body: SimulateRequest = { menus }
  let res: Response
  try {
    res = await fetch(`${API_URL}/api/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error(UNREACHABLE)
  }
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}
