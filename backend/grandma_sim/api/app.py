"""HTTP API for the frontend.

    GET    /menu                      base menu items, both bakeries
    GET    /profiles                  every day that has a profile set
    GET    /days/{day}/profile        profile in force on a day
    PUT    /days/{day}/profile        set the profile from that day onward
    DELETE /days/{day}/profile        drop it; the previous one carries over
    GET    /days/{day}/menu           menu items as they stand on a day
    GET    /days/{day}/simulation     the simulated day

Interactive docs at /docs once running.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Path, status
from fastapi.middleware.cors import CORSMiddleware

from ..menu.items import Menu, MenuItem
from ..profiles.overrides import DayProfile
from ..profiles.store import ScheduledProfile
from ..simulation.day import DayResult
from .service import SimulationService

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

DayNumber = Path(ge=1, description="Day number, starting at 1.")


def _flatten(menus: list[Menu]) -> list[MenuItem]:
    return [item for menu in menus for item in menu.items]


def create_app(
    service: SimulationService | None = None,
    cors_origins: list[str] = DEFAULT_CORS_ORIGINS,
) -> FastAPI:
    """
    Build the API around a simulation service.

    Args:
     service: The service to expose; defaults to one on ./grandma.db.
     cors_origins: Frontend origins allowed to call the API (Vite's dev
      server by default).

    Returns:
     The FastAPI app.
    """
    service = service or SimulationService()
    app = FastAPI(title="Grandma's Bakeria simulation")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/menu")
    def get_menu() -> list[MenuItem]:
        return _flatten(service.base_menus())

    @app.get("/profiles")
    def list_profiles() -> list[ScheduledProfile]:
        return service.profiles.all()

    @app.get("/days/{day}/profile")
    def get_profile(day: int = DayNumber) -> ScheduledProfile:
        return service.profile_for(day)

    @app.put("/days/{day}/profile")
    def put_profile(profile: DayProfile, day: int = DayNumber) -> ScheduledProfile:
        try:
            return service.set_profile(day, profile)
        except ValueError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error))

    @app.delete("/days/{day}/profile", status_code=status.HTTP_204_NO_CONTENT)
    def delete_profile(day: int = DayNumber) -> None:
        if not service.clear_profile(day):
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"no profile set on day {day}")

    @app.get("/days/{day}/menu")
    def get_day_menu(day: int = DayNumber) -> list[MenuItem]:
        return _flatten(service.menus_for(day))

    @app.get("/days/{day}/simulation")
    def get_simulation(day: int = DayNumber) -> DayResult:
        return service.simulate(day)

    return app
