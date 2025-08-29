from fastapi.testclient import TestClient

from app.main import create_app


def test_create_memory_endpoint_returns_created_memory():
    app = create_app()
    client = TestClient(app)

    payload = {"user_id": "u1", "content": "hello world", "source": "manual"}
    res = client.post("/api/v1/memories", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"]
    assert data["user_id"] == "u1"
    assert data["content"] == "hello world"
    assert data["source"] == "manual"
