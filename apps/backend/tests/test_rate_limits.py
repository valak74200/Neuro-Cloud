import os
from time import sleep

from app.main import create_app
from fastapi.testclient import TestClient


def test_rate_limit_per_ip_and_headers():
    # Configure a very small window for quick test
    os.environ["NC_RATE_LIMIT_MAX_REQUESTS"] = "3"
    os.environ["NC_RATE_LIMIT_WINDOW_SECONDS"] = "1"

    app = create_app()
    client = TestClient(app)

    # First three requests allowed
    for _ in range(3):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert "X-RateLimit-Limit" in r.headers
        assert "X-RateLimit-Remaining" in r.headers
        assert "X-RateLimit-Reset" in r.headers

    # Fourth should be rate limited
    r4 = client.get("/healthz")
    assert r4.status_code == 429
    assert r4.headers.get("Retry-After") is not None

    # After window reset, it should allow again (keep sleep short)
    sleep(1)
    r5 = client.get("/healthz")
    assert r5.status_code == 200
