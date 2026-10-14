from datetime import date
from decimal import Decimal

from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import (
    ListItemStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.payable_receivable_repository import (
    PayableRepository,
    ReceivableRepository,
)
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.dashboard import (
    CategoryAmount,
    DashboardData,
    DashboardSummary,
    DueItem,
    MonthPoint,
)
from app.utils.dates import month_range, month_key, today_local
from app.utils.money import money


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.payable_repo = PayableRepository(db)
        self.receivable_repo = ReceivableRepository(db)
        self.notification_repo = NotificationRepository(db)

    def build(self, user_id: str) -> DashboardData:
        today = today_local()
        month_start, month_end = month_range(today.year, today.month)

        saldo = sum(
            (self.account_repo.balance(acc) for acc in self.account_repo.get_by_user(user_id)
             if acc.active),
            Decimal("0"),
        )

        receitas = self.transaction_repo.sum_by_type(
            user_id,
            TransactionType.income,
            [TransactionStatus.received, TransactionStatus.paid],
            month_start,
            month_end,
        )
        despesas = self.transaction_repo.sum_by_type(
            user_id,
            TransactionType.expense,
            [TransactionStatus.paid, TransactionStatus.received],
            month_start,
            month_end,
        )

        payables = self.payable_repo.list_for_user(user_id)
        pending_payables = [p for p in payables if p.status == ListItemStatus.pending]
        overdue_payables = [p for p in pending_payables if p.due_date < today]
        receivables = self.receivable_repo.list_for_user(user_id)
        pending_receivables = [r for r in receivables if r.status == ListItemStatus.pending]

        summary = DashboardSummary(
            saldo_atual=money(saldo),
            receitas_mes=receitas,
            despesas_mes=despesas,
            resultado_mes=money(receitas - despesas),
            contas_a_pagar=len(pending_payables),
            contas_vencidas=len(overdue_payables),
            contas_a_receber=len(pending_receivables),
            valor_contas_a_pagar=money(sum((p.amount for p in pending_payables), Decimal("0"))),
            valor_contas_vencidas=money(sum((p.amount for p in overdue_payables), Decimal("0"))),
            valor_contas_a_receber=money(sum((r.amount for r in pending_receivables), Decimal("0"))),
            notificacoes_nao_lidas=self.notification_repo.unread_count(user_id),
        )

        gastos_categoria = self._category_expenses(user_id, month_start, month_end)
        evolucao = self._evolution(user_id, today, months=6)
        proximos = self._upcoming(today, pending_payables, pending_receivables)
        ultimas = self._recent_transactions(user_id, limit=10)

        return DashboardData(
            summary=summary,
            gastos_por_categoria=gastos_categoria,
            evolucao_mensal=evolucao,
            proximos_vencimentos=proximos,
            ultimas_movimentacoes=ultimas,
        )

    def _category_expenses(self, user_id: str, start: date, end: date) -> list[CategoryAmount]:
        rows = self.transaction_repo.group_by_category(user_id, start, end)
        cat_cache = {}
        result = []
        for row in rows:
            cid = row["category_id"]
            if cid not in cat_cache:
                cat = self.category_repo.get(Category, cid) if cid else None
                cat_cache[cid] = cat.name if cat else "Sem categoria"
            result.append(
                CategoryAmount(
                    category_id=cid,
                    category_name=cat_cache[cid],
                    amount=money(row["amount"]),
                )
            )
        return result

    def _evolution(self, user_id: str, today: date, months: int) -> list[MonthPoint]:
        points = []
        for offset in range(months - 1, -1, -1):
            year = today.year
            month = today.month - offset
            while month <= 0:
                month += 12
                year -= 1
            start, end = month_range(year, month)
            rec = self.transaction_repo.sum_by_type(
                user_id,
                TransactionType.income,
                [TransactionStatus.received, TransactionStatus.paid],
                start,
                end,
            )
            des = self.transaction_repo.sum_by_type(
                user_id,
                TransactionType.expense,
                [TransactionStatus.paid, TransactionStatus.received],
                start,
                end,
            )
            points.append(
                MonthPoint(month=month_key(start), receitas=rec, despesas=des)
            )
        return points

    def _upcoming(
        self,
        today: date,
        pending_payables,
        pending_receivables,
        days: int = 30,
    ) -> list[DueItem]:
        items = []
        for p in pending_payables:
            days_left = (p.due_date - today).days
            if days_left <= days:
                items.append(
                    DueItem(
                        id=p.id,
                        kind="payable",
                        description=p.description,
                        amount=p.amount,
                        due_date=p.due_date,
                        status=p.status.value,
                        days_left=days_left,
                    )
                )
        for r in pending_receivables:
            days_left = (r.due_date - today).days
            if days_left <= days:
                items.append(
                    DueItem(
                        id=r.id,
                        kind="receivable",
                        description=r.description,
                        amount=r.amount,
                        due_date=r.due_date,
                        status=r.status.value,
                        days_left=days_left,
                    )
                )
        items.sort(key=lambda x: x.due_date)
        return items

    def _recent_transactions(self, user_id: str, limit: int) -> list[dict]:
        txns = self.transaction_repo.list_transactions(user_id, limit=limit)
        result = []
        cats = {c.id: c.name for c in self.category_repo.get_by_user(user_id)}
        accounts = {a.id: a.name for a in self.account_repo.get_by_user(user_id)}
        for t in txns:
            if t.type == TransactionType.transfer:
                label = f"{accounts.get(t.from_account_id, '?')} → {accounts.get(t.to_account_id, '?')}"
                account_name = label
            else:
                account_name = accounts.get(t.account_id, "" if t.card_id else "?")
            result.append(
                {
                    "id": t.id,
                    "description": t.description,
                    "amount": str(t.amount),
                    "type": t.type.value,
                    "type_code": t.type.value,
                    "status": t.status.value,
                    "date": t.date.isoformat(),
                    "category": cats.get(t.category_id),
                    "account": account_name,
                }
            )
        return result