from datetime import date

from fastapi import HTTPException, status
from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import (
    ListItemStatus,
    RecurrenceFrequency,
    TransactionStatus,
    TransactionType,
)
from app.models.payable_receivable import Payable, Receivable
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.payable_receivable_repository import (
    PayableRepository,
    ReceivableRepository,
)
from app.schemas.payable_receivable import (
    PayableCreate,
    PayableRead,
    PayableUpdate,
    ReceivableCreate,
    ReceivableRead,
    ReceivableUpdate,
)
from app.utils.dates import next_occurrence, today_local
from app.utils.money import money


class PayableService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PayableRepository(db)
        self.account_repo = AccountRepository(db)

    def _validate(self, user_id: str, category_id, account_id) -> None:
        if category_id:
            cat = self.db.get(Category, category_id)
            if cat is None or cat.user_id != user_id:
                raise HTTPException(status_code=400, detail="Categoria inválida")
        if account_id:
            acc = self.db.get(Account, account_id)
            if acc is None or acc.user_id != user_id:
                raise HTTPException(status_code=400, detail="Conta inválida")

    def list(
        self,
        user_id: str,
        group: str = "todas",
    ) -> list[PayableRead]:
        today = today_local()
        all_items = self.repo.list_for_user(user_id, include_canceled=(group == "todas"))
        if group == "vencidas":
            all_items = [p for p in all_items if p.due_date < today and p.status == ListItemStatus.pending]
        elif group == "hoje":
            all_items = [p for p in all_items if p.due_date == today and p.status == ListItemStatus.pending]
        elif group == "proximas":
            all_items = [
                p for p in all_items
                if p.status == ListItemStatus.pending
                and p.due_date >= today
                and (p.due_date - today).days <= 30
            ]
        elif group == "pagas":
            all_items = [p for p in all_items if p.status == ListItemStatus.paid]
        result = []
        for p in all_items:
            read = PayableRead.model_validate(p)
            read.is_overdue = p.status == ListItemStatus.pending and p.due_date < today
            result.append(read)
        result.sort(key=lambda x: (x.status.value != "pendente", x.due_date))
        return result

    def create(self, user_id: str, data: PayableCreate) -> PayableRead:
        self._validate(user_id, data.category_id, data.account_id)
        item = Payable(
            user_id=user_id,
            description=data.description.strip(),
            amount=money(data.amount),
            due_date=data.due_date,
            category_id=data.category_id,
            account_id=data.account_id,
            frequency=data.frequency,
            observation=data.observation,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def to_read(self, item: Payable) -> PayableRead:
        read = PayableRead.model_validate(item)
        read.is_overdue = item.status == ListItemStatus.pending and item.due_date < today_local()
        return read

    def _get_owned(self, user_id: str, payable_id: str) -> Payable:
        item = self.repo.get_or_404(Payable, payable_id)
        if item.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conta a pagar não encontrada")
        return item

    def update(self, user_id: str, payable_id: str, data: PayableUpdate) -> PayableRead:
        item = self._get_owned(user_id, payable_id)
        payload = data.model_dump(exclude_unset=True)
        if "amount" in payload and payload["amount"] is not None:
            payload["amount"] = money(payload["amount"])
            self._validate(user_id, payload.get("category_id") or item.category_id, payload.get("account_id") or item.account_id)
        for field, value in payload.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def pay(self, user_id: str, payable_id: str) -> PayableRead:
        item = self._get_owned(user_id, payable_id)
        if item.status == ListItemStatus.paid:
            return self.to_read(item)
        if item.account_id:
            acc = self.db.get(Account, item.account_id)
            if acc and item.category_id:
                txn = Transaction(
                    user_id=user_id,
                    description=item.description,
                    amount=money(item.amount),
                    type=TransactionType.expense,
                    date=today_local(),
                    category_id=item.category_id,
                    account_id=item.account_id,
                    status=TransactionStatus.paid,
                    paid_at=today_local(),
                    observation=item.observation,
                )
                self.db.add(txn)
        item.status = ListItemStatus.paid
        item.paid_at = today_local()
        if item.frequency and item.frequency != RecurrenceFrequency.daily:
            nxt = self._next_payable(item)
            self.db.add(nxt)
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def _next_payable(self, item: Payable) -> Payable:
        next_due = next_occurrence(item.due_date, item.frequency.value)
        return Payable(
            user_id=item.user_id,
            description=item.description,
            amount=item.amount,
            due_date=next_due,
            category_id=item.category_id,
            account_id=item.account_id,
            frequency=item.frequency,
            observation=item.observation,
            status=ListItemStatus.pending,
        )

    def cancel(self, user_id: str, payable_id: str) -> PayableRead:
        item = self._get_owned(user_id, payable_id)
        item.status = ListItemStatus.canceled
        item.paid_at = None
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def delete(self, user_id: str, payable_id: str) -> None:
        item = self._get_owned(user_id, payable_id)
        self.db.delete(item)
        self.db.commit()


class ReceivableService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReceivableRepository(db)
        self.payable_service = PayableService(db)

    def _validate(self, user_id: str, category_id, account_id) -> None:
        self.payable_service._validate(user_id, category_id, account_id)

    def list(self, user_id: str, group: str = "todas") -> list[ReceivableRead]:
        today = today_local()
        all_items = self.repo.list_for_user(user_id, include_canceled=(group == "todas"))
        if group == "vencidos":
            all_items = [p for p in all_items if p.due_date < today and p.status == ListItemStatus.pending]
        elif group == "hoje":
            all_items = [p for p in all_items if p.due_date == today and p.status == ListItemStatus.pending]
        elif group == "proximos":
            all_items = [p for p in all_items if p.status == ListItemStatus.pending and (p.due_date - today).days <= 30 and p.due_date >= today]
        elif group == "recebidos":
            all_items = [p for p in all_items if p.status == ListItemStatus.received]
        result = []
        for r in all_items:
            read = ReceivableRead.model_validate(r)
            read.is_overdue = r.status == ListItemStatus.pending and r.due_date < today
            result.append(read)
        result.sort(key=lambda x: (x.status.value != "pendente", x.due_date))
        return result

    def create(self, user_id: str, data: ReceivableCreate) -> ReceivableRead:
        self._validate(user_id, data.category_id, data.account_id)
        item = Receivable(
            user_id=user_id,
            description=data.description.strip(),
            amount=money(data.amount),
            due_date=data.due_date,
            category_id=data.category_id,
            account_id=data.account_id,
            frequency=data.frequency,
            observation=data.observation,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def to_read(self, item: Receivable) -> ReceivableRead:
        read = ReceivableRead.model_validate(item)
        read.is_overdue = item.status == ListItemStatus.pending and item.due_date < today_local()
        return read

    def _get_owned(self, user_id: str, receivable_id: str) -> Receivable:
        item = self.repo.get_or_404(Receivable, receivable_id)
        if item.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conta a receber não encontrada")
        return item

    def update(self, user_id: str, receivable_id: str, data: ReceivableUpdate) -> ReceivableRead:
        item = self._get_owned(user_id, receivable_id)
        payload = data.model_dump(exclude_unset=True)
        if "amount" in payload and payload["amount"] is not None:
            payload["amount"] = money(payload["amount"])
        for field, value in payload.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def receive(self, user_id: str, receivable_id: str) -> ReceivableRead:
        item = self._get_owned(user_id, receivable_id)
        if item.status == ListItemStatus.received:
            return self.to_read(item)
        if item.account_id:
            if item.category_id:
                txn = Transaction(
                    user_id=user_id,
                    description=item.description,
                    amount=money(item.amount),
                    type=TransactionType.income,
                    date=today_local(),
                    category_id=item.category_id,
                    account_id=item.account_id,
                    status=TransactionStatus.received,
                    paid_at=today_local(),
                    observation=item.observation,
                )
                self.db.add(txn)
        item.status = ListItemStatus.received
        item.received_at = today_local()
        if item.frequency and item.frequency != RecurrenceFrequency.daily:
            next_due = next_occurrence(item.due_date, item.frequency.value)
            self.db.add(
                Receivable(
                    user_id=user_id,
                    description=item.description,
                    amount=item.amount,
                    due_date=next_due,
                    category_id=item.category_id,
                    account_id=item.account_id,
                    frequency=item.frequency,
                    observation=item.observation,
                    status=ListItemStatus.pending,
                )
            )
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def cancel(self, user_id: str, receivable_id: str) -> ReceivableRead:
        item = self._get_owned(user_id, receivable_id)
        item.status = ListItemStatus.canceled
        item.received_at = None
        self.db.commit()
        self.db.refresh(item)
        return self.to_read(item)

    def delete(self, user_id: str, receivable_id: str) -> None:
        item = self._get_owned(user_id, receivable_id)
        self.db.delete(item)
        self.db.commit()