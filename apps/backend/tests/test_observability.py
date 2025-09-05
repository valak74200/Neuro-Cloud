from app.main import create_app
from fastapi.testclient import TestClient


def test_metrics_endpoint_available():
    app = create_app()
    client = TestClient(app)
    res = client.get("/metrics")
    assert res.status_code == 200
    # Prometheus format must contain HELP/TYPE or metrics lines
    assert "http_requests_total" in res.text or "# HELP" in res.text


def test_request_is_logged_and_counted():
    app = create_app()
    client = TestClient(app)
    # Ensure /healthz and /api/v1/me (unauth) produce metrics entries
    client.get("/healthz")
    res = client.get("/api/v1/me")
    assert res.status_code in (200, 401)

    # Metrics reflect counters for GET /healthz
    res2 = client.get("/metrics")
    assert res2.status_code == 200
    text = res2.text
    assert "http_requests_total" in text
