from decimal import Decimal

API = "/api"


def test_search_finds_transaction(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()
    client.post(
        f"{API}/transactions",
        json={
            "description": "Supermercado Pão de Açúcar",
            "amount": 150,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Alimentação"],
            "account_id": acc["id"],
            "status": "pago",
        },
        headers=headers,
    )

    resp = client.get(f"{API}/search?q=Pão de Açúcar", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(r["description"] == "Supermercado Pão de Açúcar" for r in data["results"])


def test_search_no_results(client, auth):
    headers, _ = auth
    data = client.get(f"{API}/search?q=inexistente-xyz", headers=headers).json()
    assert data["total"] == 0


def test_notification_flow(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()
    client.post(
        f"{API}/payables",
        json={
            "description": "Internet",
            "amount": 99.90,
            "due_date": "2026-10-04",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert client.post(f"{API}/notifications/generate", headers=headers).status_code == 200

    count = client.get(f"{API}/notifications/unread-count", headers=headers).json()
    assert count["unread"] >= 1

    listed = client.get(f"{API}/notifications", headers=headers).json()
    assert listed
    first = listed[0]
    resp = client.post(f"{API}/notifications/{first['id']}/read", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


def test_notifications_require_ownership(client, auth, other_auth, categories):
    headers_a, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers_a,
    ).json()
    client.post(
        f"{API}/payables",
        json={
            "description": "Conta atrasada",
            "amount": 50,
            "due_date": "2026-10-04",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers_a,
    )
    assert client.post(f"{API}/notifications/generate", headers=headers_a).status_code == 200
    listed = client.get(f"{API}/notifications", headers=headers_a).json()
    assert listed
    nid = listed[0]["id"]

    headers_b, _ = other_auth
    assert client.post(f"{API}/notifications/{nid}/read", headers=headers_b).status_code == 404