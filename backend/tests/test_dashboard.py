from datetime import date
from decimal import Decimal

API = "/api"


def test_dashboard_summary(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Carteira", "initial_balance": 1000, "type": "conta_corrente"},
        headers=headers,
    ).json()

    today = date.today()
    client.post(
        f"{API}/transactions",
        json={
            "description": "Salário",
            "amount": 5000,
            "type": "receita",
            "date": today.isoformat(),
            "category_id": cats["Salário"],
            "account_id": acc["id"],
            "status": "recebido",
        },
        headers=headers,
    )
    client.post(
        f"{API}/transactions",
        json={
            "description": "Supermercado",
            "amount": 389.90,
            "type": "despesa",
            "date": today.isoformat(),
            "category_id": cats["Alimentação"],
            "account_id": acc["id"],
            "status": "pago",
        },
        headers=headers,
    )

    data = client.get(f"{API}/dashboard", headers=headers).json()
    summary = data["summary"]
    assert Decimal(summary["saldo_atual"]) == Decimal("5610.10")
    assert Decimal(summary["receitas_mes"]) == Decimal("5000.00")
    assert Decimal(summary["despesas_mes"]) == Decimal("389.90")
    assert Decimal(summary["resultado_mes"]) == Decimal("4610.10")

    by_cat = {c["category_name"]: c["amount"] for c in data["gastos_por_categoria"]}
    assert Decimal(by_cat["Alimentação"]) == Decimal("389.90")
    assert len(data["ultimas_movimentacoes"]) >= 2


def test_dashboard_pending_payables(client, auth, categories):
    headers, cats = categories
    acc = client.post(
        f"{API}/accounts",
        json={"name": "Conta", "initial_balance": 100, "type": "conta_corrente"},
        headers=headers,
    ).json()
    client.post(
        f"{API}/payables",
        json={
            "description": "Internet",
            "amount": 120,
            "due_date": "2026-10-25",
            "category_id": cats["Moradia"],
            "account_id": acc["id"],
        },
        headers=headers,
    )
    data = client.get(f"{API}/dashboard", headers=headers).json()
    summary = data["summary"]
    assert summary["contas_a_pagar"] == 1
    assert Decimal(summary["valor_contas_a_pagar"]) == Decimal("120.00")