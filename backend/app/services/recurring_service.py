from datetime import date

from fastapi import HTTPException
from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.enums import (
    RecurrenceStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.recurring import RecurringTransaction
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.recurring_repository import RecurringRepository
from app.schemas.recurring import (
    RecurringCreate,
    RecurringRead,
    RecurringUpdate,
)
from app.utils.dates import next_occurrence, today_local
from app.utils.money import money


class RecurringService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecurringRepository(db)

    def _validate_links(self, user_id: str, category_id, account_id, card_id) -> None:
        if category_id:
            cat = self.db.get(Category, category_id)
            if cat is None or cat.user_id != user_id:
                raise HTTPException(status_code=400, detail="Categoria inválida")
        if account_id:
            acc = self.db.get(Account, account_id)
            if acc is None or acc.user_id != user_id:
                raise HTTPException(status_code=400, detail="Conta inválida")
        if card_id:
            card = self.db.get(CreditCard, card_id)
            if card is None or card.user_id != user_id:
                raise HTTPException(status_code=400, detail="Cartão inválido")

    def list(self, user_id: str) -> list[RecurringRead]:
        records = self.repo.list_for_user(user_id)
        result = []
        for r in records:
            read = RecurringRead.model_validate(r)
            read.generated_count = self.repo.generated_count(user_id, r.id)
            result.append(read)
        return result

    def get(self, user_id: str, recurring_id: str) -> RecurringRead:
        record = self.repo.get_or_404(RecurringTransaction, recurring_id)
        if record.user_id != user_id:
            raise HTTPException(status_code=404, detail="Recorrência não encontrada")
        read = RecurringRead.model_validate(record)
        read.generated_count = self.repo.generated_count(user_id, record.id)
        return read

    def create(self, user_id: str, data: RecurringCreate) -> RecurringRead:
        self._validate_links(user_id, data.category_id, data.account_id, data.card_id)
        if data.end_date and data.end_date < data.start_date:
            raise HTTPException(status_code=400, detail="Data final anterior à inicial")
        record = RecurringTransaction(
            user_id=user_id,
            description=data.description.strip(),
            type=data.type,
            amount=money(data.amount),
            frequency=data.frequency,
            start_date=data.start_date,
            end_date=data.end_date,
            next_due_date=data.start_date,
            category_id=data.category_id,
            account_id=data.account_id,
            card_id=data.card_id,
            status=RecurrenceStatus.active,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self.get(user_id, record.id)

    def update(self, user_id: str, recurring_id: str, data: RecurringUpdate) -> RecurringRead:
        record = self.repo.get_or_404(RecurringTransaction, recurring_id)
        if record.user_id != user_id:
            raise HTTPException(status_code=404, detail="Recorrência não encontrada")
        payload = data.model_dump(exclude_unset=True)
        if "amount" in payload:
            payload["amount"] = money(payload["amount"])
        self._validate_links(
            user_id,
            payload.get("category_id", record.category_id),
            payload.get("account_id", record.account_id),
            payload.get("card_id", record.card_id),
        )
        for field, value in payload.items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return self.get(user_id, record.id)

    def delete(self, user_id: str, recurring_id: str) -> None:
        record = self.repo.get_or_404(RecurringTransaction, recurring_id)
        if record.user_id != user_id:
            raise HTTPException(status_code=404, detail="Recorrência não encontrada")
        self.db.delete(record)
        self.db.commit()

    def process(self, user_id: str, until: date | None = None) -> list[Transaction]:
        """Gera os lançamentos recorrentes vencidos/em aberto até a data limite."""
        today = today_local()
        until = until or today
        created: list[Transaction] = []
        for record in self.repo.active_records(user_id):
            while record.next_due_date <= until:
                if record.end_date and record.next_due_date > record.end_date:
                    record.status = RecurrenceStatus.canceled
                    break
                status_value = (
                    TransactionStatus.paid
                    if (record.type == TransactionType.expense and record.card_id is None and record.next_due_date <= today)
                    else TransactionStatus.pending
                )
                status_value = (
                    TransactionStatus.received
                    if (record.type == TransactionType.income and record.next_due_date <= today)
                    else status_value
                )
                if record.type == TransactionType.expense and record.card_id:
                    status_value = TransactionStatus.pending
                txn = Transaction(
                    user_id=user_id,
                    description=record.description,
                    amount=record.amount,
                    type=record.type,
                    date=record.next_due_date,
                    category_id=record.category_id,
                    account_id=record.account_id,
                    card_id=record.card_id,
                    status=status_value,
                    paid_at=record.next_due_date if status_value in (
                        TransactionStatus.paid, TransactionStatus.received
                    ) else None,
                    recurring_id=record.id,
                )
                self.db.add(txn)
                created.append(txn)
                record.next_due_date = next_occurrence(record.next_due_date, record.frequency.value)
                record.last_generated_at = record.next_due_date
        self.db.commit()
        return created