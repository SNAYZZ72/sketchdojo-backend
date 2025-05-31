# =============================================================================
# app/api/v1/router.py
# =============================================================================
from fastapi import APIRouter

from app.api.v1.endpoints import auth, characters, panels, projects, tasks
from app.api.v1.endpoints import websocket as ws
from app.api.v1.endpoints import webtoons

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(webtoons.router, prefix="/webtoons", tags=["webtoons"])
router.include_router(panels.router, prefix="/panels", tags=["panels"])
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(ws.router, prefix="/ws", tags=["websocket"])
