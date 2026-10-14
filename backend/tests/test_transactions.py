from datetime import date
from decimal import Decimal

API = "/api"


def _mk_account(client, headers, name="Conta", initial=0):
    resp = client.post(
        f"{API}/accounts",
        json={"name": name, "initial_balance": initial, "type": "conta_corrente"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def _mk_card(client, headers, account_id):
    resp = client.post(
        f"{API}/cards",
        json={
            "name": "Visa",
            "bank": "Itaú",
            "limit_amount": 5000,
            "closing_day": 5,
            "due_day": 12,
            "account_id": account_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_reject_installment_without_card(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    resp = client.post(
        f"{API}/transactions",
        json={
            "description": "Notebook",
            "amount": 3000,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "account_id": acc["id"],
            "installments_total": 3,
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_installment_creates_all_parcels(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    card = _mk_card(client, headers, acc["id"])

    resp = client.post(
        f"{API}/transactions",
        json={
            "description": "iPhone",
            "amount": 1200,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "card_id": card["id"],
            "installments_total": 6,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    first = resp.json()
    assert first["installment_number"] == 1
    assert Decimal(first["amount"]) == Decimal("200.00")

    all_txns = client.get(
        f"{API}/transactions?card_id={card['id']}&limit=50", headers=headers
    ).json()
    assert len(all_txns) == 6
    total = sum(Decimal(t["amount"]) for t in all_txns)
    assert total == Decimal("1200.00")
    assert all(t["status"] == "pendente" for t in all_txns)


def test_card_used_limit_reflects_pending(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    card = _mk_card(client, headers, acc["id"])

    client.post(
        f"{API}/transactions",
        json={
            "description": "Notebook",
            "amount": 3000,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "card_id": card["id"],
            "installments_total": 3,
        },
        headers=headers,
    )
    refreshed = client.get(f"{API}/cards/{card['id']}", headers=headers).json()
    assert Decimal(refreshed["used_limit"]) == Decimal("3000.00")
    assert Decimal(refreshed["available_limit"]) == Decimal("2000.00")


def test_card_expense_ignores_account_balance(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers, initial=5000)
    card = _mk_card(client, headers, acc["id"])
    client.post(
        f"{API}/transactions",
        json={
            "description": "Airbnb",
            "amount": 800,
            "type": "despesa",
            "date": "2026-10-02",
            "category_id": cats["Moradia"],
            "card_id": card["id"],
        },
        headers=headers,
    )
    balance = client.get(f"{API}/accounts/{acc['id']}", headers=headers).json()["balance"]
    assert Decimal(balance) == Decimal("5000.00")


def test_pay_invoice_creates_expense_and_settles(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers, initial=5000)
    card = _mk_card(client, headers, acc["id"])
    client.post(
        f"{API}/transactions",
        json={
            "description": "Presente",
            "amount": 600,
            "type": "despesa",
            "date": "2026-09-15",
            "category_id": cats["Compras"],
            "card_id": card["id"],
        },
        headers=headers,
    )

    invoices = client.get(f"{API}/cards/{card['id']}/invoices", headers=headers).json()
    month = next(
        i["month"] for i in invoices if Decimal(i["total"]) == Decimal("600.00")
    )

    resp = client.post(f"{API}/cards/{card['id']}/invoices/{month}/pay", headers=headers)
    assert resp.status_code == 200
    result = resp.json()
    assert Decimal(result["paid_total"]) == Decimal("600.00")

    invoices_after = client.get(f"{API}/cards/{card['id']}/invoices", headers=headers).json()
    paid = next(i for i in invoices_after if i["month"] == month)
    assert Decimal(paid["total"]) == Decimal("0.00")

    # Gera lançamento de despesa "Fatura de cartão" na conta vinculada
    txns = client.get(f"{API}/transactions?limit=50", headers=headers).json()
    fatura = next(t for t in txns if t["description"].startswith("Pagamento de fatura"))
    assert fatura["category_id"]
    assert Decimal(fatura["amount"]) == Decimal("600.00")
    assert fatura["status"] == "pago"
    assert fatura["account_id"] == acc["id"]


def test_delete_installment_parcel_is_rejected(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)
    card = _mk_card(client, headers, acc["id"])

    first = client.post(
        f"{API}/transactions",
        json={
            "description": "Sofa",
            "amount": 900,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "card_id": card["id"],
            "installments_total": 3,
        },
        headers=headers,
    ).json()

    resp = client.delete(f"{API}/transactions/{first['id']}", headers=headers)
    assert resp.status_code == 400

    parcels = client.get(
        f"{API}/transactions?card_id={card['id']}&limit=50", headers=headers
    ).json()
    assert len(parcels) == 3

    groups = client.get(f"{API}/installments", headers=headers).json()
    assert len(groups) == 1
    assert len(groups[0]["parcels"]) == 3


def test_delete_plain_transaction_still_works(client, auth, categories):
    headers, cats = categories
    acc = _mk_account(client, headers)

    txn = client.post(
        f"{API}/transactions",
        json={
            "description": "Cafe",
            "amount": 15,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "account_id": acc["id"],
        },
        headers=headers,
    ).json()

    resp = client.delete(f"{API}/transactions/{txn['id']}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"{API}/transactions/{txn['id']}", headers=headers).status_code == 404


def test_foreign_transaction_not_visible(client, auth, other_auth, categories):
    headers_a, cats = categories
    acc = _mk_account(client, headers_a)
    card = _mk_card(client, headers_a, acc["id"])
    txn = client.post(
        f"{API}/transactions",
        json={
            "description": "Segredo",
            "amount": 10,
            "type": "despesa",
            "date": "2026-10-01",
            "category_id": cats["Compras"],
            "card_id": card["id"],
        },
        headers=headers_a,
    ).json()

    headers_b, _ = other_auth
    assert client.get(f"{API}/transactions/{txn['id']}", headers=headers_b).status_code == 404
    listed = client.get(f"{API}/transactions", headers=headers_b).json()
    assert all(item["id"] != txn["id"] for item in listed)