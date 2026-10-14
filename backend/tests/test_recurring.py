API = "/api"


def test_recurring_create_and_process(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()

    resp = client.post(
        f"{API}/recurring",
        json={
            "description": "Streaming",
            "type": "despesa",
            "amount": 45.90,
            "frequency": "mensal",
            "start_date": "2026-10-01",
            "category_id": cats["Assinaturas"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["frequency"] == "mensal"

    listed = client.get(f"{API}/recurring", headers=headers).json()
    assert any(r["id"] == rec["id"] for r in listed)

    process = client.post(f"{API}/recurring/process?until=2026-12-31", headers=headers)
    assert process.status_code == 200
    assert process.json()["generated"] >= 1

    txns = client.get(f"{API}/transactions?limit=50", headers=headers).json()
    assert any(t["description"] == "Streaming" for t in txns)


def test_recurring_delete(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()
    rec = client.post(
        f"{API}/recurring",
        json={
            "description": "Academia",
            "type": "despesa",
            "amount": 80,
            "frequency": "mensal",
            "start_date": "2026-10-01",
            "category_id": cats["Lazer"],
            "account_id": acc["id"],
        },
        headers=headers,
    ).json()
    assert client.delete(f"{API}/recurring/{rec['id']}", headers=headers).status_code == 204
    assert client.get(f"{API}/recurring/{rec['id']}", headers=headers).status_code == 404


def test_recurring_ownership(client, auth, other_auth, categories):
    headers_a, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers_a,
    ).json()
    rec = client.post(
        f"{API}/recurring",
        json={
            "description": "Plano",
            "type": "despesa",
            "amount": 30,
            "frequency": "mensal",
            "start_date": "2026-10-01",
            "category_id": cats["Assinaturas"],
            "account_id": acc["id"],
        },
        headers=headers_a,
    ).json()

    headers_b, _ = other_auth
    assert client.get(f"{API}/recurring/{rec['id']}", headers=headers_b).status_code == 404