from decimal import Decimal

API = "/api"


def _mk_account(client, headers):
    resp = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 1000, "type": "conta_corrente"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_payable_lifecycle(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)

    resp = client.post(
        f"{API}/payables",
        json={
            "description": "Aluguel",
            "amount": 850,
            "due_date": "2026-10-10",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["status"] == "pendente"
    assert item["is_overdue"] is False

    assert client.post(f"{API}/payables/{item['id']}/pay", headers=headers).status_code == 200
    paid = client.get(f"{API}/payables?group=pagas", headers=headers).json()
    assert any(p["id"] == item["id"] and p["status"] == "pago" for p in paid)

    resp_reopen = client.post(f"{API}/payables/{item['id']}/reopen", headers=headers)
    assert resp_reopen.status_code == 200
    assert resp_reopen.json()["status"] == "pendente"


def test_overdue_payable_flag(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    resp = client.post(
        f"{API}/payables",
        json={
            "description": "Conta antiga",
            "amount": 120,
            "due_date": "2026-09-30",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_overdue"] is True


def test_paying_payable_moves_money(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    payable = client.post(
        f"{API}/payables",
        json={
            "description": "IPTU",
            "amount": 250,
            "due_date": "2026-10-05",
            "category_id": cats["Impostos"],
            "account_id": acc["id"],
        },
        headers=headers,
    ).json()

    before = Decimal(client.get(f"{API}/accounts/{acc['id']}", headers=headers).json()["balance"])
    assert client.post(f"{API}/payables/{payable['id']}/pay", headers=headers).status_code == 200
    after = Decimal(client.get(f"{API}/accounts/{acc['id']}", headers=headers).json()["balance"])
    assert before - after == Decimal("250.00")


def test_receivable_lifecycle(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    resp = client.post(
        f"{API}/receivables",
        json={
            "description": "Freela",
            "amount": 900,
            "due_date": "2026-10-20",
            "category_id": cats["Freelance"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    item = resp.json()

    before = Decimal(client.get(f"{API}/accounts/{acc['id']}", headers=headers).json()["balance"])
    assert client.post(f"{API}/receivables/{item['id']}/receive", headers=headers).status_code == 200
    received = client.get(f"{API}/receivables?group=recebidos", headers=headers).json()
    assert any(r["id"] == item["id"] and r["status"] == "recebido" for r in received)

    after = Decimal(client.get(f"{API}/accounts/{acc['id']}", headers=headers).json()["balance"])
    assert after - before == Decimal("900.00")