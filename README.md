# Grandma Must Win

The big chain has moved in next door. Its menu looks awfully familiar, its prices are suspiciously low, and Grandma's regulars are already eyeing the door.

Can you keep the neighborhood on her side?

<p align="center">
  <img width="1180" alt="Grandma Must Win game screen" src="https://github.com/user-attachments/assets/d6cafe41-03f3-4732-87ef-84fd6876a84c" />
</p>

[![Play Grandma Must Win](https://img.shields.io/badge/Play-Grandma%20Must%20Win-ff3f25?style=for-the-badge)](https://grandmamustwin.vercel.app)

## Play a day

Set the prices and portions on both menus, then open the doors. Customers arrive through the day with their own tastes, budgets, allergies, and routines. Watch the shops compete for each order, then see how Grandma did when the day's over.

Grandma's view keeps the results simple. Switch to **Grandchild** for the numbers behind them: item sales, busy hours, customer groups, costs, and profit. The simulation uses the menus you set, so a price change or a new pastry can shift who buys what.

## Run it on your machine

You'll need [Node.js](https://nodejs.org/) and [uv](https://docs.astral.sh/uv/). Start the backend and frontend in separate terminals from the project folder.

Terminal one:

```bash
cd backend
uv sync
uv run python -m grandma_sim.api
```

Terminal two:

```bash
cd frontend
npm ci
npm run dev
```

Open the local address Vite prints (usually `http://localhost:5173`). The frontend sends the day's menus to the API at `http://localhost:8000` and replays the results in the browser.

To work on the interface without starting the backend, run `VITE_USE_MOCK=1 npm run dev` from `frontend/`. That uses the saved sample day; menu edits won't affect its results.

## Under the counter

- [`frontend/`](frontend/README.md) — React and TypeScript game interface.
- [`backend/`](backend/README.md) — Python customer, menu, and bakery simulation, plus the API.

The detailed backend guide covers API routes, customer behavior, recipes, ingredient costs, and multi-day seasons. For a quick single-day replay, run `uv run python run_simulation.py --seed 0` from `backend/`.
