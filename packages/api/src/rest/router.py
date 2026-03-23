"""REST API router — mounts all sub-routers under /api/v1."""

from fastapi import APIRouter

from src.rest.controllers.activity import router as activity_router
from src.rest.controllers.analysis import router as analysis_router
from src.rest.controllers.conventions import router as conventions_router
from src.rest.controllers.decisions import router as decisions_router
from src.rest.controllers.entities import router as entities_router
from src.rest.controllers.projects import router as projects_router
from src.rest.controllers.relationships import router as relationships_router
from src.rest.controllers.search import router as search_router
from src.rest.controllers.settings import router as settings_router
from src.rest.controllers.webhooks import router as webhooks_router

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    """API root — confirms the API is running."""
    return {"service": "semantic-canvas", "version": "0.1.0"}


# Webhooks (not project-scoped)
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

# Projects (top-level CRUD)
router.include_router(projects_router, prefix="/projects", tags=["projects"])

# Project-scoped resources
_project = "/projects/{project_id}"
router.include_router(entities_router, prefix=f"{_project}/entities", tags=["entities"])
router.include_router(relationships_router, prefix=f"{_project}/relationships", tags=["relationships"])
router.include_router(decisions_router, prefix=f"{_project}/decisions", tags=["decisions"])
router.include_router(conventions_router, prefix=f"{_project}/conventions", tags=["conventions"])
router.include_router(activity_router, prefix=f"{_project}/activity", tags=["activity"])
router.include_router(search_router, prefix=f"{_project}/search", tags=["search"])
router.include_router(analysis_router, prefix=_project, tags=["analysis"])
router.include_router(settings_router, prefix=_project, tags=["settings"])
