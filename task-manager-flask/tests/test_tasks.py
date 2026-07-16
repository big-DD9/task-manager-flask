def test_create_task_requires_auth(client):
    resp = client.post("/tasks/", json={"title": "Buy milk"})
    assert resp.status_code == 401


def test_create_and_get_task(client, auth_headers):
    resp = client.post("/tasks/", json={"title": "Buy milk"}, headers=auth_headers)
    assert resp.status_code == 201
    task = resp.get_json()
    assert task["title"] == "Buy milk"
    assert task["status"] == "pending"

    resp2 = client.get(f"/tasks/{task['id']}", headers=auth_headers)
    assert resp2.status_code == 200
    assert resp2.get_json()["id"] == task["id"]


def test_create_task_missing_title_rejected(client, auth_headers):
    resp = client.post("/tasks/", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_create_task_invalid_status_rejected(client, auth_headers):
    resp = client.post(
        "/tasks/", json={"title": "x", "status": "not_a_real_status"}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_list_tasks_filters_by_status(client, auth_headers):
    client.post("/tasks/", json={"title": "A", "status": "pending"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "B", "status": "done"}, headers=auth_headers)

    resp = client.get("/tasks/?status=done", headers=auth_headers)
    results = resp.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "B"


def test_update_task(client, auth_headers):
    create = client.post("/tasks/", json={"title": "Old"}, headers=auth_headers)
    task_id = create.get_json()["id"]

    resp = client.put(
        f"/tasks/{task_id}", json={"status": "done"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "done"
    assert resp.get_json()["title"] == "Old"


def test_delete_task(client, auth_headers):
    create = client.post("/tasks/", json={"title": "Temp"}, headers=auth_headers)
    task_id = create.get_json()["id"]

    resp = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp2 = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert resp2.status_code == 404


def test_users_cannot_see_each_others_tasks(client):
    client.post("/auth/register", json={
        "name": "User1", "email": "u1@example.com", "password": "password123"
    })
    login1 = client.post("/auth/login", json={
        "email": "u1@example.com", "password": "password123"
    })
    headers1 = {"Authorization": f"Bearer {login1.get_json()['access_token']}"}

    client.post("/auth/register", json={
        "name": "User2", "email": "u2@example.com", "password": "password123"
    })
    login2 = client.post("/auth/login", json={
        "email": "u2@example.com", "password": "password123"
    })
    headers2 = {"Authorization": f"Bearer {login2.get_json()['access_token']}"}

    create = client.post("/tasks/", json={"title": "Secret"}, headers=headers1)
    task_id = create.get_json()["id"]

    # User2 should not be able to see User1's task
    resp = client.get(f"/tasks/{task_id}", headers=headers2)
    assert resp.status_code == 404

    resp_list = client.get("/tasks/", headers=headers2)
    assert resp_list.get_json() == []
