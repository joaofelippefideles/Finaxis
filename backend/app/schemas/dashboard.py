from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    saldo_atual: Decimal = Decimal("0")
    receitas_mes: Decimal = Decimal("0")
    despesas_mes: Decimal = Decimal("0")
    resultado_mes: Decimal = Decimal("0")
    contas_a_pagar: int = 0
    contas_vencidas: int = 0
    contas_a_receber: int = 0
    valor_contas_a_pagar: Decimal = Decimal("0")
    valor_contas_vencidas: Decimal = Decimal("0")
    valor_contas_a_receber: Decimal = Decimal("0")
    cartoes_em_uso: int = 0
    notificacoes_nao_lidas: int = 0


class CategoryAmount(BaseModel):
    category_id: Optional[str] = None
    category_name: str
    amount: Decimal = Decimal("0")


class MonthPoint(BaseModel):
    month: str
    receitas: Decimal = Decimal("0")
    despesas: Decimal = Decimal("0")


class DueItem(BaseModel):
    id: str
    kind: str  # payable | receivable
    description: str
    amount: Decimal = Decimal("0")
    due_date: date
    status: str
    days_left: int = 0


class DashboardData(BaseModel):
    summary: DashboardSummary
    gastos_por_categoria: list[CategoryAmount] = []
    evolucao_mensal: list[MonthPoint] = []
    proximos_vencimentos: list[DueItem] = []
    ultimas_movimentacoes: list[dict] = []