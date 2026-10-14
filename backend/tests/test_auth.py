API = "/api"


def test_register_returns_token(client):
    resp = client.post(
        f"{API}/auth/register",
        json={"name": "Joana", "email": "joana@example.com", "password": "abc12345"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["email"] == "joana@example.com"
    assert data["user"]["name"] == "Joana"


def test_duplicate_email_conflict(client):
    payload = {"name": "Ana", "email": "dupe@example.com", "password": "abc12345"}
    assert client.post(f"{API}/auth/register", json=payload).status_code == 201
    resp = client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_success(client, auth):
    headers, user = auth
    email = user["email"]
    resp = client.post(
        f"{API}/auth/login", json={"email": email, "password": "senha123"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password(client, auth):
    _, user = auth
    resp = client.post(
        f"{API}/auth/login", json={"email": user["email"], "password": "errada"}
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_me_returns_payload(client, auth):
    headers, user = auth
    resp = client.get(f"{API}/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]


def test_logout(client, auth):
    headers, _ = auth
    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 204