import pytest
import os
from fastapi.testclient import TestClient
from platform_core.server import app
from client.db import init_db, get_connection

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth_db():
    init_db()


def test_auth_rejects_invalid_api_key():
    resp = client.get("/v1/mydata", headers={"x-api-key": "invalid-key-999"})
    assert resp.status_code == 401
    assert "Invalid API Key" in resp.json()["detail"]


def test_auth_accepts_valid_api_key():
    resp = client.get("/v1/health", headers={"x-api-key": "sk-test-key-123"})
    assert resp.status_code == 200


def test_cors_allowed_origin():
    resp = client.options("/v1/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_disallowed_origin_in_production(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

    from platform_core.server import origins
    assert "http://malicious-site.com" not in origins
    assert "http://localhost:3000" in origins


def test_production_db_initialization_does_not_seed_static_key(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("XENIA_TEST_MODE", "0")
    monkeypatch.delenv("XENIA_API_KEY", raising=False)
    monkeypatch.delenv("DEV_API_KEY", raising=False)

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tenants")
    conn.commit()
    conn.close()

    init_db()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT api_key FROM tenants WHERE id = 'tenant-local'")
    key = c.fetchone()[0]
    conn.close()

    assert key.startswith("sk-xenia-")
    assert key != "sk-test-key-123"
