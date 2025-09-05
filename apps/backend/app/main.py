from app.infrastructure.observability.observability import setup_observability
from app.routers.v1 import api as api_v1
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Neuro-Cloud API", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(api_v1, prefix="/api/v1")
    setup_observability(app)
    return app


app = create_app()
