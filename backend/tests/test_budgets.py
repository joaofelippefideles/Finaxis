from decimal import Decimal

API = "/api"


def test_budget_create_and_summary(client, auth, categories):
    headers, cats = categories
    resp = client.post(
        f"{API}/budgets",
        json={"category_id": cats["Alimentação"], "limit_amount": 1000, "month": "2026-10"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert Decimal(resp.json()["limit_amount"]) == Decimal("1000.00")

    summary = client.get(f"{API}/budgets?month=2026-10", headers=headers).json()
    assert summary["month"] == "2026-10"
    assert Decimal(summary["total_limit"]) == Decimal("1000.00")
    assert len(summary["items"]) == 1


def test_duplicate_budget_conflict(client, auth, categories):
    headers, cats = categories
    payload = {"category_id": cats["Lazer"], "limit_amount": 300, "month": "2026-10"}
    assert client.post(f"{API}/budgets", json=payload, headers=headers).status_code == 201
    assert client.post(f"{API}/budgets", json=payload, headers=headers).status_code == 409


def test_budget_usage_tracks_spending(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 2000, "type": "conta_corrente"},
        headers=headers,
    ).json()
    client.post(
        f"{API}/budgets",
        json={"category_id": cats["Alimentação"], "limit_amount": 500, "month": "2026-10"},
        headers=headers,
    )
    client.post(
        f"{API}/transactions",
        json={
            "description": "Mercado",
            "amount": 300,
            "type": "despesa",
            "date": "2026-10-03",
            "category_id": cats["Alimentação"],
            "account_id": acc["id"],
            "status": "pago",
        },
        headers=headers,
    )
    summary = client.get(f"{API}/budgets?month=2026-10", headers=headers).json()
    item = summary["items"][0]
    assert Decimal(item["spent"]) == Decimal("300.00")
    assert Decimal(item["remaining"]) == Decimal("200.00")
    assert Decimal(item["percent"]) == Decimal("60.00")


def test_budget_update_and_delete(client, auth, categories):
    headers, cats = categories
    budget = client.post(
        f"{API}/budgets",
        json={"category_id": cats["Saúde"], "limit_amount": 100, "month": "2026-11"},
        headers=headers,
    ).json()

    resp = client.put(
        f"{API}/budgets/{budget['id']}",
        json={"limit_amount": 250},
        headers=headers,
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["limit_amount"]) == Decimal("250.00")

    resp = client.delete(f"{API}/budgets/{budget['id']}", headers=headers)
    assert resp.status_code == 204
    summary = client.get(f"{API}/budgets?month=2026-11", headers=headers).json()
    assert summary["items"] == []