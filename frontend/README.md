# Bakery price simulator: frontend

React + TypeScript + Vite + Mantine. A street view of the two bakeries with an editable menu for each. **Start** sends both menus to the backend and receives the schedule for the whole day.

```bash
npm install
npm run dev                   # http://localhost:5173, proxies /api to http://localhost:8000
VITE_USE_MOCK=1 npm run dev   # no backend: Start returns sample_data/day_seed0.json
npm run build
```

`VITE_API_URL` overrides the backend origin (default: same origin, via the dev proxy).

## Backend contract: `POST /api/simulate`

The backend has no HTTP layer yet; this is what the frontend sends and expects.

**Request** (JSON)

```jsonc
{
  "menus": [
    { "bakery": "the_bakery",       "items": [ /* MenuItem, ... */ ] },
    { "bakery": "grandmas_bakeria", "items": [ /* MenuItem, ... */ ] }
  ],
  "seed": 0                // optional; the frontend doesn't send it yet
}
```

Each `MenuItem` is the backend pydantic model as JSON (see `src/types.ts`): `id`, `name`, `bakery`, `category`, `description`, `flavor {sweet_savoury, bitterness, fruitiness, categories[]}`, `price`, `portion_size_g`, `allergens[]`, `daypart_weights {}`. A bakery's `items` can be empty. New items get an `id` made from their name, and `daypart_weights` may be `{}` (unlisted dayparts count as 0.5).

**Response 200**: the backend's `DayResult` as-is, with the same shape as `sample_data/day_seed0.json`: `{config, customers, events, summary}`. The schedule is `events`, in time order. Each event is `{minute, time: "HH:MM", daypart, customer_id, segment, choice}`, where `choice.purchased` is false for a customer who walked away.

**Errors**: any non-2xx. A JSON `{"detail": "..."}` (FastAPI's default, including 422 validation errors) is shown to the user; anything else shows "Backend error (status)".

### Reference implementation (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel
from grandma_sim import DayConfig, DayResult, DaySimulator, Menu

class SimulateRequest(BaseModel):
    menus: list[Menu]
    seed: int = 0

app = FastAPI()

@app.post("/api/simulate")
def simulate(req: SimulateRequest) -> DayResult:
    return DaySimulator(DayConfig(seed=req.seed), req.menus).run()
```

Run with `uvicorn app:app --port 8000`. Check that computed fields (`choice.purchased`, `breakdown.total`, `summary.purchases`) appear in the JSON, since the frontend reads them.

## Data

`sample_data/menus.json` holds the seed menus and the default clock, generated from `grandma_sim.menu.seed.build_menus()` and `DayClock()`. `sample_data/day_seed0.json` is a full simulated day written by `backend/run_simulation.py --json`.
