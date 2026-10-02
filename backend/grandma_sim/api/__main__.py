"""Serve the API.

    uv run python -m grandma_sim.api [--host 127.0.0.1] [--port 8000] [--db grandma.db]
"""

import argparse

import uvicorn

from ..menu.store import DEFAULT_DB_PATH
from .app import create_app
from .service import SimulationService


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the simulation API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite file to use")
    args = parser.parse_args()

    uvicorn.run(create_app(SimulationService(args.db)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
