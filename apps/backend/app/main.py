from app.infrastructure.rate_limit.limiter import RateLimitMiddleware
from app.routers.v1 import api as api_v1
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Neuro-Cloud API",
        version="0.1.0",
        description="API du cloud mémoire personnel Neuro-Cloud (DDD, FastAPI)",
        contact={
            "name": "Neuro-Cloud",
            "url": "https://github.com/valak74200/Neuro-Cloud",
        },
        license_info={"name": "MIT"},
        openapi_tags=[
            {"name": "health", "description": "Endpoints de santé"},
            {"name": "auth", "description": "Endpoints liés à l'authentification"},
            {"name": "memories", "description": "CRUD des souvenirs"},
        ],
    )

    @app.get("/healthz", tags=["health"], summary="Vérifie la santé du service")
    def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(api_v1, prefix="/api/v1")
    app.add_middleware(RateLimitMiddleware)
    return app


app = create_app()
