"""REST API router — mounts all sub-routers under /api/v1."""

from fastapi import APIRouter

from src.rest.controllers.webhooks import router as webhooks_router

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    """API root — confirms the API is running."""
    return {"service": "semantic-canvas", "version": "0.1.0"}


router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

# Sub-routers will be added as they're built:
# from src.rest.controllers.entities import router as entities_router
# from src.rest.controllers.projects import router as projects_router
# router.include_router(entities_router, prefix="/entities", tags=["entities"])
# router.include_router(projects_router, prefix="/projects", tags=["projects"])
