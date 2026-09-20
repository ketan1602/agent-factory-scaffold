from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard.routes import demo, health, metrics
from dashboard.routes import eval as eval_router

app = FastAPI(title="Agent Factory — Repo 07", version="0.1.0")

app.include_router(health.router)
app.include_router(demo.router)
app.include_router(metrics.router)
app.include_router(eval_router.router)

_static = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(_static), html=True), name="static")
