"""
DoorDash-like Food Delivery API — entry point.
Run with: cd /workspace && python -m uvicorn doordash_app.main:app --reload
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Module aliasing — ensures bare 'import models' and 'from doordash_app.models'
# reference the same module object and therefore the same in-memory dicts.
# This is needed when tests add doordash_app/ to sys.path and import via both
# bare names ('models', 'main') and package names ('doordash_app.models').
# ---------------------------------------------------------------------------
import doordash_app.models as _pkg_models
sys.modules.setdefault("models", _pkg_models)

from doordash_app.routers import restaurants, menu, cart, orders, users

app = FastAPI(
    title="DoorDash-like Food Delivery API",
    description="A DoorDash-inspired food delivery app with restaurants, menus, cart, and orders.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — permissive for demo; tighten in production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(restaurants.router)
app.include_router(menu.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(users.router)

# ---------------------------------------------------------------------------
# Static files — served from ./static at /static
# Only mount when the directory exists so tests/dev work without it.
# ---------------------------------------------------------------------------
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["frontend"], include_in_schema=False)
def serve_index() -> FileResponse:
    """Serve the frontend SPA home page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    # Graceful fallback when the UX engineer's files haven't landed yet
    return JSONResponse(
        {"status": "ok", "service": "DoorDash API", "note": "Frontend not yet deployed"},
        status_code=200,
    )


@app.get("/api/health", tags=["health"])
def health_check() -> dict:
    """Health-check endpoint — confirms the API is running."""
    return {"status": "ok", "service": "DoorDash Food Delivery API"}
