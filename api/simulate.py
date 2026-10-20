"""Vercel function for the frontend's standalone day simulation endpoint."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from grandma_sim.api.app import SimulateRequest
from grandma_sim.api.service import SimulationService

service = SimulationService(db_path="/tmp/grandma-socratica-vercel.db")


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            request = SimulateRequest.model_validate_json(self.rfile.read(length))
            result = service.simulate_menus(request.menus, request.seed)
            response = JSONResponse(content=jsonable_encoder(result))
        except ValidationError as error:
            response = JSONResponse(
                status_code=422,
                content={"detail": json.loads(error.json())},
            )
        except ValueError as error:
            response = JSONResponse(status_code=422, content={"detail": str(error)})

        self.send_response(response.status_code)
        self.send_header("Content-Type", response.media_type or "application/json")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)
