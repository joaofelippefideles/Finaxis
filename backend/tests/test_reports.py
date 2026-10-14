from datetime import date
from decimal import Decimal

API = "/api"


def _seed(client, headers, cats):
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()
    today = date.today().isoformat()
    client.post(
        f"{API}/transactions",
        json={
            "description": "Salário",
            "amount": 4000,
            "type": "receita",
            "date": today,
            "category_id": cats["Salário"],
            "account_id": acc["id"],
            "status": "recebido",
        },
        headers=headers,
    )
    client.post(
        f"{API}/transactions",
        json={
            "description": "Mercado",
            "amount": 500,
            "type": "despesa",
            "date": today,
            "category_id": cats["Alimentação"],
            "account_id": acc["id"],
            "status": "pago",
        },
        headers=headers,
    )
    return acc


def test_report_summary(client, auth, categories):
    headers, cats = categories
    _seed(client, headers, cats)
    resp = client.get(
        f"{API}/reports/summary?start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 200
    rep = resp.json()
    assert Decimal(rep["total_receitas"]) == Decimal("4000.00")
    assert Decimal(rep["total_despesas"]) == Decimal("500.00")
    assert Decimal(rep["resultado"]) == Decimal("3500.00")


def test_report_budget_vs_realized_filters_by_category(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 0, "type": "conta_corrente"},
        headers=headers,
    ).json()

    for name, amount in (("Alimentação", "500.00"), ("Transporte", "200.00")):
        resp = client.post(
            f"{API}/transactions",
            json={
                "description": f"Gasto {name}",
                "amount": amount,
                "type": "despesa",
                "date": "2026-10-15",
                "category_id": cats[name],
                "account_id": acc["id"],
                "status": "pago",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text

    for name, limit in (
        ("Alimentação", "1000.00"),
        ("Transporte", "1000.00"),
        ("Moradia", "500.00"),
    ):
        resp = client.post(
            f"{API}/budgets",
            json={"category_id": cats[name], "limit_amount": limit},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text

    resp = client.get(
        f"{API}/reports/summary?start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    rows = {r["category"]: r for r in resp.json()["orcamento_vs_realizado"]}
    assert Decimal(rows["Alimentação"]["spent"]) == Decimal("500.00")
    assert Decimal(rows["Transporte"]["spent"]) == Decimal("200.00")
    assert Decimal(rows["Moradia"]["spent"]) == Decimal("0.00")


def test_report_export_csv(client, auth, categories):
    headers, cats = categories
    _seed(client, headers, cats)
    resp = client.get(
        f"{API}/reports/export?fmt=csv&start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert b"Sal\xc3\xa1rio" in resp.content or "Salário".encode() in resp.content


def test_report_export_xlsx(client, auth, categories):
    headers, cats = categories
    _seed(client, headers, cats)
    resp = client.get(
        f"{API}/reports/export?fmt=xlsx&start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 200
    assert (
        "spreadsheet" in resp.headers["content-type"]
        or resp.content[:2] == b"PK"
    )


def test_report_export_pdf(client, auth, categories):
    headers, cats = categories
    _seed(client, headers, cats)
    resp = client.get(
        f"{API}/reports/export?fmt=pdf&start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_report_export_bad_format(client, auth, categories):
    headers, cats = categories
    resp = client.get(
        f"{API}/reports/export?fmt=doc&start_date=2026-09-01&end_date=2026-12-31",
        headers=headers,
    )
    assert resp.status_code == 422