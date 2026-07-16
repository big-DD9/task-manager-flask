import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app(env="testing")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Registers a user and returns Authorization headers with a valid JWT."""
    client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "supersecret123"
    })
    resp = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "supersecret123"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
