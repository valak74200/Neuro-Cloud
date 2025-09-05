from app.main import create_app
from fastapi.testclient import TestClient


def test_openapi_has_tags_and_summaries():
    app = create_app()
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    doc = r.json()
    # Tags present
    names = {t["name"] for t in doc.get("tags", [])}
    assert {"health", "auth", "memories"}.issubset(names)

    # Summaries on main endpoints
    get_me = doc["paths"]["/api/v1/me"]["get"]
    assert get_me.get("summary")
    list_mem = doc["paths"]["/api/v1/memories"]["get"]
    assert list_mem.get("summary")
    create_mem = doc["paths"]["/api/v1/memories"]["post"]
    assert create_mem.get("summary")
