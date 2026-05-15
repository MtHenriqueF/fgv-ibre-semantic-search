"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes import (
    document_routes,
    evaluation_routes,
    health_routes,
    metadata_routes,
    search_routes,
)
from src.config import PROJECT_ROOT


FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_INDEX_PATH = FRONTEND_DIR / "index.html"


def create_app() -> FastAPI:
    app = FastAPI(
        title="FGV IBRE Semantic Search API",
        description="API para busca semântica e avaliação do corpus de notícias.",
    )
    app.include_router(health_routes.router)
    app.include_router(search_routes.router)
    app.include_router(metadata_routes.router)
    app.include_router(document_routes.router)
    app.include_router(evaluation_routes.router)

    if FRONTEND_INDEX_PATH.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )
    else:

        @app.get("/", include_in_schema=False)
        async def api_root() -> dict[str, str]:
            return {
                "message": "FGV IBRE Semantic Search API",
                "docs": "/docs",
            }

    return app


app = create_app()
