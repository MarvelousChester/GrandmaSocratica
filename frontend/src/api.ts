import { MOCK_MENU } from './mockMenu'
import type { MenuItem } from './types'

// The backend has no HTTP layer yet. When it does, replace the body with:
//   const res = await fetch(`${import.meta.env.VITE_API_URL}/menu`)
//   return res.json()
export async function fetchMenu(): Promise<MenuItem[]> {
  return MOCK_MENU
}
