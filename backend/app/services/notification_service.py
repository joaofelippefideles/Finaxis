from decimal import Decimal
from typing import Optional

from app.database.session import Session

from app.models.enums import (
    ListItemStatus,
    NotificationType,
    TransactionStatus,
)
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.repositories.payable_receivable_repository import (
    PayableRepository,
    ReceivableRepository,
)
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.credit_card_repository import CreditCardRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.utils.dates import today_local
from app.utils.money import money


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
        self.payable_repo = PayableRepository(db)
        self.receivable_repo = ReceivableRepository(db)
        self.card_repo = CreditCardRepository(db)
        self.budget_repo = BudgetRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)

    def _existing(self, user_id: str, ntype: str, ref: str) -> bool:
        for n in self.repo.list_for_user(user_id, limit=10000):
            if n.type == ntype and n.data and n.data.get("ref") == ref and not n.is_read:
                return True
        return False

    def add(self, user_id: str, ntype: NotificationType, title: str, message: str, ref: Optional[str] = None, data: Optional[dict] = None) -> None:
        if ref and self._existing(user_id, ntype.value, ref):
            return
        payload = dict(data or {})
        if ref:
            payload["ref"] = ref
        self.db.add(
            Notification(
                user_id=user_id,
                type=ntype,
                title=title,
                message=message,
                data=payload,
                is_read=False,
            )
        )

    def generate(self, user_id: str) -> int:
        """Gera notificações de acordo com as regras de alerta do sistema."""
        today = today_local()
        before = self.repo.unread_count(user_id)

        payables = self.payable_repo.list_for_user(user_id)
        for p in payables:
            if p.status != ListItemStatus.pending:
                continue
            days = (p.due_date - today).days
            if days < 0 and abs(days) <= 7:
                self.add(
                    user_id, NotificationType.payable_due,
                    "Conta vencida",
                    f'"{p.description}" venceu em {p.due_date.strftime("%d/%m/%Y")}',
                    ref=f"payable:{p.id}", data={"payable_id": p.id},
                )
            elif 0 <= days <= 7:
                self.add(
                    user_id, NotificationType.payable_soon,
                    "Conta próxima do vencimento",
                    f'"{p.description}" vence em {p.due_date.strftime("%d/%m/%Y")} '
                    f"({days} dia{'s' if days != 1 else ''})",
                    ref=f"payable:{p.id}", data={"payable_id": p.id},
                )

        receivables = self.receivable_repo.list_for_user(user_id)
        for r in receivables:
            if r.status != ListItemStatus.pending:
                continue
            days = (r.due_date - today).days
            if days < 0 and abs(days) <= 7:
                self.add(
                    user_id, NotificationType.receivable_due,
                    "Recebimento vencido",
                    f'"{r.description}" venceu em {r.due_date.strftime("%d/%m/%Y")}',
                    ref=f"receivable:{r.id}", data={"receivable_id": r.id},
                )
            elif 0 <= days <= 7:
                self.add(
                    user_id, NotificationType.receivable_soon,
                    "Recebimento próximo",
                    f'"{r.description}" vence em {r.due_date.strftime("%d/%m/%Y")}',
                    ref=f"receivable:{r.id}", data={"receivable_id": r.id},
                )

        for card in self.card_repo.get_by_user(user_id):
            used = self.card_repo.used_limit(card)
            limit = money(card.limit_amount)
            if limit > 0 and used >= money(limit * Decimal("0.9")):
                pct = (used / limit * 100)
                self.add(
                    user_id, NotificationType.card_limit,
                    "Cartão próximo do limite",
                    f'O cartão "{card.name}" está com {pct:.0f}% do limite utilizado',
                    ref=f"card:{card.id}", data={"card_id": card.id},
                )

        budgets = self.budget_repo.list_for_user(user_id)
        month = today.strftime("%Y-%m")
        for b in budgets:
            if b.month and b.month != month:
                continue
            spent = self._category_spent(user_id, b.category_id, today)
            limit = money(b.limit_amount)
            if limit <= 0:
                continue
            pct = (spent / limit * 100)
            if pct >= 100:
                self.add(
                    user_id, NotificationType.budget_warning,
                    "Orçamento estourado",
                    f"Orçamento de {self._category_name(user_id, b.category_id)} "
                    f"ultrapassou o limite ({pct:.0f}%)",
                    ref=f"budget:{b.id}", data={"budget_id": b.id},
                )
            elif pct >= 90:
                self.add(
                    user_id, NotificationType.budget_warning,
                    "Orçamento no limite",
                    f"Orçamento de {self._category_name(user_id, b.category_id)} "
                    f"utilizado em {pct:.0f}%",
                    ref=f"budget:{b.id}", data={"budget_id": b.id},
                )

        self.db.commit()
        return self.repo.unread_count(user_id) - before

    def _category_spent(self, user_id: str, category_id: str, today) -> Decimal:
        from app.utils.dates import month_range

        start, end = month_range(today.year, today.month)
        return self._spent_sql(user_id, category_id, start, end)

    def _spent_sql(self, user_id: str, category_id: str, start, end) -> Decimal:
        from app.models.enums import TransactionType
        from app.models.transaction import Transaction

        total = Decimal("0")
        for t in self.db.all(Transaction):
            if (
                t.user_id == user_id
                and t.category_id == category_id
                and t.type == TransactionType.expense
                and t.status in (TransactionStatus.paid, TransactionStatus.received)
                and start <= t.date <= end
            ):
                total += t.amount
        return total

    def _category_name(self, user_id: str, category_id: str) -> str:
        from app.models.category import Category

        cat = self.category_repo.get(Category, category_id)
        return cat.name if cat else "?"

    def list(self, user_id: str, limit: int = 50) -> list[Notification]:
        return self.repo.list_for_user(user_id, limit)

    def mark_read(self, user_id: str, notification_id: str) -> Notification:
        n = self.repo.get_or_404(Notification, notification_id)
        if n.user_id != user_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        n.is_read = True
        self.db.commit()
        self.db.refresh(n)
        return n

    def mark_all_read(self, user_id: str) -> None:
        self.repo.mark_all_read(user_id)

    def unread_count(self, user_id: str) -> int:
        return self.repo.unread_count(user_id)