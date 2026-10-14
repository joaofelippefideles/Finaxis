from datetime import date
from decimal import Decimal

from app.database.session import Session

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.enums import (
    TransactionStatus,
    TransactionType,
)
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.report import ReportData, ReportQuery
from app.utils.dates import month_key
from app.utils.money import money


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.category_repo = CategoryRepository(db)

    def _effective(self, ttype_: TransactionType) -> list[TransactionStatus]:
        if ttype_ == TransactionType.income:
            return [TransactionStatus.received, TransactionStatus.paid]
        return [TransactionStatus.paid, TransactionStatus.received]

    def build(self, user_id: str, query: ReportQuery) -> ReportData:
        if query.start_date > query.end_date:
            raise ValueError("Data inicial deve ser anterior à final")

        receitas = self.repo.sum_by_type(
            user_id,
            TransactionType.income,
            self._effective(TransactionType.income),
            query.start_date,
            query.end_date,
        )
        despesas = self.repo.sum_by_type(
            user_id,
            TransactionType.expense,
            self._effective(TransactionType.expense),
            query.start_date,
            query.end_date,
        )

        lancamentos = self._transactions_as_dict(user_id, query)
        cats = {c.id: c.name for c in self.category_repo.get_by_user(user_id)}
        contas = {a.id: a.name for a in self.db.all(Account) if a.user_id == user_id}
        cartoes = {c.id: c.name for c in self.db.all(CreditCard) if c.user_id == user_id}

        for item in lancamentos:
            item["category"] = cats.get(item.get("category_id"))
            item["account"] = contas.get(item.get("account_id")) or (item.get("type") == "transferencia" and f"{contas.get(item.get('from_account_id'),'')} → {contas.get(item.get('to_account_id'),'')}")
            item["card"] = cartoes.get(item.get("card_id"))

        return ReportData(
            query=query,
            total_receitas=receitas,
            total_despesas=despesas,
            resultado=money(receitas - despesas),
            por_categoria=self._by_dimension(user_id, query, "category_id", cats),
            por_conta=self._by_dimension(user_id, query, "account_id", contas),
            por_cartao=self._by_dimension(user_id, query, "card_id", cartoes),
            evolucao_mensal=self._monthly_evolution(user_id, query),
            fluxo_caixa=self._cash_flow(user_id, query),
            comparativo_anual=self._yearly_comparison(user_id, query),
            orcamento_vs_realizado=self._budget_vs_realized(user_id, query),
            lancamentos=lancamentos,
        )

    def _transactions_as_dict(self, user_id: str, query: ReportQuery) -> list[dict]:
        rows = self.repo.list_transactions(
            user_id,
            start_date=query.start_date,
            end_date=query.end_date,
            ttype=query.type or None,
            status=query.status or None,
            category_id=query.category_id,
            account_id=query.account_id,
            card_id=query.card_id,
        )
        result = []
        for t in rows:
            result.append(
                {
                    "id": t.id,
                    "description": t.description,
                    "amount": str(t.amount),
                    "type": t.type.value,
                    "status": t.status.value,
                    "date": t.date.isoformat(),
                    "category_id": t.category_id,
                    "account_id": t.account_id,
                    "from_account_id": t.from_account_id,
                    "to_account_id": t.to_account_id,
                    "card_id": t.card_id,
                }
            )
        return result

    def _by_dimension(self, user_id: str, query: ReportQuery, dim: str, names: dict) -> list[dict]:
        valid = set(
            self._effective(TransactionType.income)
            + self._effective(TransactionType.expense)
        )
        ttype_filter = TransactionType(query.type) if query.type else None

        grouped: dict[tuple, dict] = {}
        for t in self.db.all(Transaction):
            if t.user_id != user_id:
                continue
            if not (query.start_date <= t.date <= query.end_date):
                continue
            if t.status not in valid:
                continue
            if query.category_id and t.category_id != query.category_id:
                continue
            if query.account_id and query.account_id not in (
                t.account_id,
                t.from_account_id,
                t.to_account_id,
            ):
                continue
            if query.card_id and t.card_id != query.card_id:
                continue
            if ttype_filter and t.type != ttype_filter:
                continue
            dim_id = getattr(t, dim)
            key = (dim_id, t.type.value)
            entry = grouped.setdefault(
                key,
                {"id": dim_id, "name": names.get(dim_id, "—"), t.type.value: Decimal("0")},
            )
            entry[t.type.value] = money(entry.get(t.type.value, Decimal("0")) + t.amount)
        return list(grouped.values())

    def _monthly_evolution(self, user_id: str, query: ReportQuery) -> list[dict]:
        start = query.start_date.replace(day=1)
        cursor = start
        result = []
        while cursor <= query.end_date:
            if cursor.month == 12:
                nxt = cursor.replace(year=cursor.year + 1, month=1)
            else:
                nxt = cursor.replace(month=cursor.month + 1)
            last_day = _last_day_of(nxt)
            rec = self.repo.sum_by_type(
                user_id, TransactionType.income, self._effective(TransactionType.income), cursor, last_day
            )
            des = self.repo.sum_by_type(
                user_id, TransactionType.expense, self._effective(TransactionType.expense), cursor, last_day
            )
            result.append(
                {
                    "month": month_key(cursor),
                    "receitas": str(rec),
                    "despesas": str(des),
                    "resultado": str(money(rec - des)),
                }
            )
            cursor = nxt
        return result

    def _cash_flow(self, user_id: str, query: ReportQuery) -> list[dict]:
        rows = self.repo.list_transactions(
            user_id, start_date=query.start_date, end_date=query.end_date
        )
        rows = list(
            filter(
                lambda t: (
                    t.status in self._effective(TransactionType.income)
                    or t.status in self._effective(TransactionType.expense)
                    or (t.type == TransactionType.transfer and t.status != TransactionStatus.canceled)
                ),
                rows,
            )
        )
        running = Decimal("0")
        flow = []
        for t in sorted(rows, key=lambda x: (x.date, x.created_at)):
            delta = Decimal("0")
            if t.type == TransactionType.income:
                delta = t.amount
            elif t.type == TransactionType.expense:
                delta = -t.amount
            running = money(running + delta)
            flow.append(
                {
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "type": t.type.value,
                    "amount": str(t.amount),
                    "running_balance": str(running),
                }
            )
        return flow

    def _yearly_comparison(self, user_id: str, query: ReportQuery) -> list[dict]:
        year = query.end_date.year
        end = date(year, 12, 31)
        result = []
        for month_num in range(1, 13):
            s = date(year, month_num, 1)
            e = _last_day_of(date(year, month_num, 1))
            rec = self.repo.sum_by_type(
                user_id, TransactionType.income, self._effective(TransactionType.income), s, e
            )
            des = self.repo.sum_by_type(
                user_id, TransactionType.expense, self._effective(TransactionType.expense), s, e
            )
            result.append(
                {
                    "month": month_num,
                    "label": f"{month_num:02d}/{year}",
                    "receitas": str(rec),
                    "despesas": str(des),
                    "resultado": str(money(rec - des)),
                }
            )
        return result

    def _budget_vs_realized(self, user_id: str, query: ReportQuery) -> list[dict]:
        budgets = [b for b in self.db.all(Budget) if b.user_id == user_id]
        cats = {c.id: c.name for c in self.category_repo.get_by_user(user_id)}
        month = month_key(query.end_date)
        result = []
        for b in budgets:
            if b.month and b.month != month:
                continue
            spent = self.repo.sum_by_type(
                user_id,
                TransactionType.expense,
                self._effective(TransactionType.expense),
                query.start_date,
                query.end_date,
                category_id=b.category_id,
            )
            limit = money(b.limit_amount)
            pct = money(spent / limit * 100) if limit else Decimal("0")
            result.append(
                {
                    "category_id": b.category_id,
                    "category": cats.get(b.category_id, "?"),
                    "limit": str(limit),
                    "spent": str(money(spent)),
                    "remaining": str(money(limit - spent)),
                    "percent": str(pct),
                }
            )
        return result


__all__ = ["ReportService"]


def _last_day_of(month_first_day: date) -> date:
    from calendar import monthrange

    year, month = month_first_day.year, month_first_day.month
    return date(year, month, monthrange(year, month)[1])