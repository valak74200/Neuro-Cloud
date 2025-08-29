from app.main import create_app
from fastapi.testclient import TestClient


def test_openapi_schema_available():
    app = create_app()
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json().get("openapi")
