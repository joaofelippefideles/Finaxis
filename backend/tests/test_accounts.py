from decimal import Decimal

API = "/api"


def _balance(client, headers, account_id):
    resp = client.get(f"{API}/accounts/{account_id}", headers=headers)
    assert resp.status_code == 200
    return Decimal(resp.json()["balance"])


def test_account_create_and_balance(client, auth):
    headers, _ = auth
    resp = client.post(
        f"{API}/accounts",
        json={"name": "Principal", "bank": "Nubank", "type": "conta_corrente", "initial_balance": 1000},
        headers=headers,
    )
    assert resp.status_code == 201
    acc = resp.json()
    assert Decimal(acc["balance"]) == Decimal("1000.00")
    assert acc["name"] == "Principal"


def test_income_reflects_balance(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()

    resp = client.post(
        f"{API}/transactions",
        json={
            "description": "Salário",
            "amount": 2500,
            "type": "receita",
            "date": "2026-10-01",
            "category_id": cats["Salário"],
            "account_id": acc["id"],
            "status": "recebido",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert _balance(client, headers, acc["id"]) == Decimal("2500.00")


def test_pending_expense_does_not_change_balance(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 1000, "type": "conta_corrente"},
        headers=headers,
    ).json()
    resp = client.post(
        f"{API}/transactions",
        json={
            "description": "Energia",
            "amount": 150,
            "type": "despesa",
            "date": "2026-10-15",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert _balance(client, headers, acc["id"]) == Decimal("1000.00")


def test_pay_transaction_updates_balance(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 1000, "type": "conta_corrente"},
        headers=headers,
    ).json()
    txn = client.post(
        f"{API}/transactions",
        json={
            "description": "Fatura luz",
            "amount": 200,
            "type": "despesa",
            "date": "2026-10-05",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    ).json()
    assert _balance(client, headers, acc["id"]) == Decimal("1000.00")

    resp = client.post(f"{API}/transactions/{txn['id']}/pay", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "pago"
    assert _balance(client, headers, acc["id"]) == Decimal("800.00")


def test_transfer_between_accounts(client, auth, categories):
    headers, _ = categories
    a = client.post(
        f"{API}/accounts",
        json={"name": "A", "initial_balance": 1000, "type": "conta_corrente"},
        headers=headers,
    ).json()
    b = client.post(
        f"{API}/accounts",
        json={"name": "B", "initial_balance": 0, "type": "poupanca"},
        headers=headers,
    ).json()

    resp = client.post(
        f"{API}/transfers",
        json={"description": "Reserva", "amount": 300, "from_account_id": a["id"], "to_account_id": b["id"], "date": "2026-10-03"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert _balance(client, headers, a["id"]) == Decimal("700.00")
    assert _balance(client, headers, b["id"]) == Decimal("300.00")


def test_same_account_transfer_rejected(client, auth, categories):
    headers, _ = categories
    a = client.post(
        f"{API}/accounts",
        json={"name": "A", "initial_balance": 100, "type": "conta_corrente"},
        headers=headers,
    ).json()
    resp = client.post(
        f"{API}/transfers",
        json={"description": "x", "amount": 10, "from_account_id": a["id"], "to_account_id": a["id"], "date": "2026-10-03"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_delete_account(client, auth):
    headers, _ = auth
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Descartável", "initial_balance": 0, "type": "carteira"},
        headers=headers,
    ).json()
    resp = client.delete(f"{API}/accounts/{acc['id']}", headers=headers)
    assert resp.status_code == 204
    listed = client.get(f"{API}/accounts", headers=headers).json()
    assert all(item["id"] != acc["id"] for item in listed)


def test_foreign_account_not_accessible(client, auth, other_auth):
    headers_a, _ = auth
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta A", "initial_balance": 100, "type": "conta_corrente"},
        headers=headers_a,
    ).json()
    headers_b, _ = other_auth
    assert client.get(f"{API}/accounts/{acc['id']}", headers=headers_b).status_code == 404