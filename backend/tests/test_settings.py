API = "/api"


def test_get_settings(client, auth):
    headers, user = auth
    resp = client.get(f"{API}/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["email"] == user["email"]
    assert data["preferences"]["currency"] == "BRL"


def test_update_preferences(client, auth):
    headers, _ = auth
    resp = client.put(
        f"{API}/settings/preferences",
        json={"currency": "USD", "date_format": "MM/DD/YYYY", "locale": "en_US"},
        headers=headers,
    )
    assert resp.status_code == 200
    prefs = client.get(f"{API}/settings", headers=headers).json()["preferences"]
    assert prefs["currency"] == "USD"


def test_update_profile(client, auth):
    headers, _ = auth
    resp = client.put(
        f"{API}/settings/profile",
        json={"name": "Novo Nome"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo Nome"


def test_change_password_flow(client, auth):
    headers, user = auth
    resp = client.put(
        f"{API}/settings/password",
        json={"current_password": "senha123", "new_password": "novaSenha456"},
        headers=headers,
    )
    assert resp.status_code == 200

    # Login antigo falha
    old = client.post(f"{API}/auth/login", json={"email": user["email"], "password": "senha123"})
    assert old.status_code == 401

    # Login novo funciona
    new = client.post(
        f"{API}/auth/login",
        json={"email": user["email"], "password": "novaSenha456"},
    )
    assert new.status_code == 200


def test_change_password_wrong_current(client, auth):
    headers, _ = auth
    resp = client.put(
        f"{API}/settings/password",
        json={"current_password": "errada", "new_password": "novaSenha456"},
        headers=headers,
    )
    assert resp.status_code in (400, 401)