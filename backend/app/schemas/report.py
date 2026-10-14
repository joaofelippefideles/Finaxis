from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ReportQuery(BaseModel):
    start_date: date
    end_date: date
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class ReportData(BaseModel):
    query: ReportQuery
    total_receitas: Decimal = Decimal("0")
    total_despesas: Decimal = Decimal("0")
    resultado: Decimal = Decimal("0")
    por_categoria: list[dict] = []
    por_conta: list[dict] = []
    por_cartao: list[dict] = []
    evolucao_mensal: list[dict] = []
    fluxo_caixa: list[dict] = []
    comparativo_anual: list[dict] = []
    orcamento_vs_realizado: list[dict] = []
    lancamentos: list[dict] = []


class ExportInfo(BaseModel):
    format: str
    filename: str
    content_type: str
    rows: int = 0