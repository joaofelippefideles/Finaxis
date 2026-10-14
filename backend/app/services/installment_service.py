from decimal import Decimal

from fastapi import HTTPException, status

from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.enums import (
    InstallmentStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.installment import Installment
from app.models.transaction import Transaction
from app.repositories.installment_repository import InstallmentRepository
from app.schemas.installment import InstallmentCreate, InstallmentRead
from app.utils.dates import add_months
from app.utils.money import money, split_installment_value


class InstallmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InstallmentRepository(db)

    def list(self, user_id: str) -> list[InstallmentRead]:
        groups = self.repo.list_for_user(user_id)
        return [self.to_read(user_id, g) for g in groups]

    def get(self, user_id: str, installments_id: str) -> InstallmentRead:
        group = self.repo.get_for_user(user_id, installments_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Compra parcelada não encontrada")
        return self.to_read(user_id, group)

    def to_read(self, user_id: str, group: Installment) -> InstallmentRead:
        parcels = [
            t
            for t in self.db.all(Transaction)
            if t.user_id == user_id and t.installment_id == group.id
        ]
        parcels.sort(key=lambda t: t.installment_number or 0)
        paid = [t for t in parcels if t.status in (TransactionStatus.paid, TransactionStatus.received)]
        paid_total = money(sum((t.amount for t in paid), Decimal("0")))
        status = InstallmentStatus.completed if len(paid) == len(parcels) and parcels else group.status
        return InstallmentRead(
            id=group.id,
            user_id=group.user_id,
            description=group.description,
            total_value=group.total_value,
            installments_total=group.installments_total,
            first_due_date=group.first_due_date,
            category_id=group.category_id,
            card_id=group.card_id,
            status=status,
            observation=group.observation,
            paid_count=len(paid),
            paid_total=paid_total,
            parcels=parcels,
        )

    def create(self, user_id: str, data: InstallmentCreate) -> InstallmentRead:
        if data.category_id and not self._owns(Category, user_id, data.category_id):
            raise HTTPException(status_code=400, detail="Categoria inválida")
        if data.card_id and not self._owns(CreditCard, user_id, data.card_id):
            raise HTTPException(status_code=400, detail="Cartão inválido")

        total = money(data.total_value)
        parcel_values = split_installment_value(total, data.installments_total)
        group = Installment(
            user_id=user_id,
            description=data.description.strip(),
            total_value=total,
            installments_total=data.installments_total,
            first_due_date=data.first_due_date,
            category_id=data.category_id,
            card_id=data.card_id,
            observation=data.observation,
        )
        self.db.add(group)
        self.db.flush()
        for i, pv in enumerate(parcel_values, start=1):
            due = add_months(data.first_due_date, i - 1)
            self.db.add(
                Transaction(
                    user_id=user_id,
                    description=f"{data.description.strip()} ({i}/{data.installments_total})",
                    amount=pv,
                    type=TransactionType.expense,
                    date=due,
                    category_id=data.category_id,
                    card_id=data.card_id,
                    status=TransactionStatus.pending,
                    observation=data.observation,
                    installment_id=group.id,
                    installment_number=i,
                    installments_total=data.installments_total,
                    is_installment=True,
                )
            )
        self.db.commit()
        return self.to_read(user_id, group)

    def delete(self, user_id: str, installments_id: str) -> None:
        group = self.repo.get_for_user(user_id, installments_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Compra parcelada não encontrada")
        parcels = [
            t
            for t in self.db.all(Transaction)
            if t.user_id == user_id and t.installment_id == group.id
        ]
        for txn in parcels:
            self.db.delete(txn)
        self.db.delete(group)
        self.db.commit()

    def _owns(self, model, user_id: str, record_id: str) -> bool:
        obj = self.db.get(model, record_id)
        return obj is not None and obj.user_id == user_id