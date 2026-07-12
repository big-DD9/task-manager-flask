def test_register_success(client):
    resp = client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "strongpassword"
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["user"]["email"] == "alice@example.com"
    assert "access_token" in body


def test_register_duplicate_email_rejected(client):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "strongpassword"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


def test_register_short_password_rejected(client):
    resp = client.post("/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "short"
    })
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/auth/register", json={
        "name": "Bob", "email": "bob@example.com", "password": "strongpassword"
    })
    resp = client.post("/auth/login", json={
        "email": "bob@example.com", "password": "strongpassword"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={
        "name": "Bob", "email": "bob@example.com", "password": "strongpassword"
    })
    resp = client.post("/auth/login", json={
        "email": "bob@example.com", "password": "wrongpassword"
    })
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "test@example.com"
