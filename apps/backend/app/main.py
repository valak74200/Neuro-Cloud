from fastapi import FastAPI

from app.routers.v1 import api as api_v1


def create_app() -> FastAPI:
    app = FastAPI(title="Neuro-Cloud API", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(api_v1, prefix="/api/v1")
    return app


app = create_app()
