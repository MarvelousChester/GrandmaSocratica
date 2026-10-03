"""HTTP API for the frontend.

    GET    /menu                      base menu items, both bakeries
    GET    /profiles                  every day that has a profile set
    GET    /days/{day}/profile        profile in force on a day
    PUT    /days/{day}/profile        set the profile from that day onward
    DELETE /days/{day}/profile        drop it; the previous one carries over
    GET    /days/{day}/menu           menu items as they stand on a day
    GET    /days/{day}/simulation     the simulated day, ledger included
    GET    /days/{day}/ledger         just the day's costs, profit and ingredients
    GET    /season?through=N          days 0..N: prices, sales, ledger, repricings

    GET    /ingredients               base ingredient prices, per bakery
    GET    /ingredient-prices         every day that has ingredient prices set
    GET    /days/{day}/ingredient-prices   ingredient price changes in force on a day
    PUT    /days/{day}/ingredient-prices   set them from that day onward
    DELETE /days/{day}/ingredient-prices   drop them; the previous ones carry over
    GET    /days/{day}/ingredients    ingredient prices as they stand on a day

    POST   /api/simulate              one standalone day for menus sent in the body

Days count from 0 (opening day). Every day is part of one season, so The
Bakery's repricing in response to earlier days is already applied.
`/api/simulate` is the exception: the frontend's editor sends whole menus and
gets one day back, with no season around it.
Interactive docs at /docs once running.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.enums import Bakery
from ..menu.costing import Pantry
from ..menu.items import Menu, MenuItem
from ..profiles.ingredients import IngredientPrices
from ..profiles.overrides import DayProfile
from ..profiles.store import ScheduledIngredientPrices, ScheduledProfile
from ..simulation.day import DayResult
from ..simulation.ledger import DayLedger
from ..simulation.season import SeasonResult
from .service import SimulationService

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

DayNumber = Path(ge=0, description="Day number; 0 is opening day.")


class SimulateRequest(BaseModel):
    menus: list[Menu] = Field(description="Up to one menu per bakery; items may be empty.")
    seed: int = Field(0, ge=0, description="Varies arrivals and choices.")


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
        return service.list_profiles()

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

    @app.get("/days/{day}/ledger")
    def get_ledger(day: int = DayNumber) -> DayLedger:
        return service.simulate(day).ledger

    @app.get("/season")
    def get_season(
        through: int = Query(ge=0, description="Last day to include."),
    ) -> SeasonResult:
        return service.season(through)

    @app.get("/ingredients")
    def get_ingredients() -> dict[Bakery, Pantry]:
        return service.base_pantries()

    @app.get("/ingredient-prices")
    def list_ingredient_prices() -> list[ScheduledIngredientPrices]:
        return service.list_ingredient_prices()

    @app.get("/days/{day}/ingredient-prices")
    def get_ingredient_prices(day: int = DayNumber) -> ScheduledIngredientPrices:
        return service.ingredient_prices_for(day)

    @app.put("/days/{day}/ingredient-prices")
    def put_ingredient_prices(
        prices: IngredientPrices, day: int = DayNumber
    ) -> ScheduledIngredientPrices:
        try:
            return service.set_ingredient_prices(day, prices)
        except ValueError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error))

    @app.delete("/days/{day}/ingredient-prices", status_code=status.HTTP_204_NO_CONTENT)
    def delete_ingredient_prices(day: int = DayNumber) -> None:
        if not service.clear_ingredient_prices(day):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"no ingredient prices set on day {day}"
            )

    @app.get("/days/{day}/ingredients")
    def get_day_ingredients(day: int = DayNumber) -> dict[Bakery, Pantry]:
        return service.pantries_for(day)

    @app.post("/api/simulate")
    def simulate_menus(request: SimulateRequest) -> DayResult:
        try:
            return service.simulate_menus(request.menus, request.seed)
        except ValueError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error))

    return app
