from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.enums import TransactionStatus, TransactionType
from app.models.installment import Installment
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.credit_card_repository import CreditCardRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransferCreate,
)
from app.utils.dates import add_months
from app.utils.money import money, split_installment_value


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)
        self.card_repo = CreditCardRepository(db)

    def _get_owned_account(self, user_id: str, account_id: Optional[str]) -> Account | None:
        if not account_id:
            return None
        account = self.account_repo.get(Account, account_id)
        if account is None or account.user_id != user_id:
            raise HTTPException(status_code=400, detail="Conta inválida")
        return account

    def _validate_ownership(
        self,
        user_id: str,
        category_id: Optional[str],
        account_id: Optional[str],
        card_id: Optional[str],
        from_account_id: Optional[str] = None,
        to_account_id: Optional[str] = None,
    ) -> None:
        if category_id:
            cat = self.category_repo.get(Category, category_id)
            if cat is None or cat.user_id != user_id or not cat.active:
                raise HTTPException(status_code=400, detail="Categoria inválida")
        for acc_id in (account_id, from_account_id, to_account_id):
            if acc_id:
                self._get_owned_account(user_id, acc_id)
        if card_id:
            card = self.card_repo.get(CreditCard, card_id)
            if card is None or card.user_id != user_id:
                raise HTTPException(status_code=400, detail="Cartão inválido")

    def create(self, user_id: str, data: TransactionCreate) -> Transaction:
        if data.type == TransactionType.transfer:
            raise HTTPException(
                status_code=400,
                detail="Use o endpoint de transferências para este tipo",
            )
        effective_account = (
            None if (data.type == TransactionType.expense and data.card_id) else data.account_id
        )
        self._validate_ownership(
            user_id, data.category_id, effective_account, data.card_id
        )
        if (
            data.installments_total
            and data.type == TransactionType.expense
            and data.card_id
        ):
            return self.create_installments(user_id, data)
        if data.installments_total and data.type == TransactionType.income:
            raise HTTPException(
                status_code=400, detail="Receitas não podem ser parceladas"
            )
        if data.installments_total and not data.card_id:
            raise HTTPException(
                status_code=400,
                detail="Parcelamento é permitido apenas para compras no cartão de crédito",
            )

        transaction = self._build_transaction(user_id, data)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def _build_transaction(
        self, user_id: str, data: TransactionCreate, amount: Optional[Decimal] = None
    ) -> Transaction:
        status_value = data.status
        is_card_expense = data.type == TransactionType.expense and data.card_id is not None
        if is_card_expense and status_value == TransactionStatus.paid:
            status_value = TransactionStatus.pending
        effective_account = (
            None if is_card_expense else data.account_id
        )
        paid_at = (
            data.date
            if status_value in (TransactionStatus.paid, TransactionStatus.received)
            else None
        )
        return Transaction(
            user_id=user_id,
            description=data.description.strip(),
            amount=money(amount if amount is not None else data.amount),
            type=data.type,
            date=data.date,
            category_id=data.category_id,
            account_id=effective_account,
            card_id=data.card_id,
            status=status_value,
            observation=data.observation,
            paid_at=paid_at,
            is_installment=data.is_installment or False,
        )

    def create_installments(self, user_id: str, data: TransactionCreate) -> Transaction:
        """Cria compra parcelada: grupo + parcelas geradas automaticamente."""
        total = money(data.amount)
        parcel_values = split_installment_value(total, data.installments_total)

        installment = Installment(
            user_id=user_id,
            description=data.description.strip(),
            total_value=total,
            installments_total=data.installments_total,
            first_due_date=data.date,
            category_id=data.category_id,
            card_id=data.card_id,
            observation=data.observation,
        )
        self.db.add(installment)
        self.db.flush()

        created: Transaction | None = None
        for i, parcel_value in enumerate(parcel_values, start=1):
            due = add_months(data.date, i - 1)
            txn = Transaction(
                user_id=user_id,
                description=f"{data.description.strip()} ({i}/{data.installments_total})",
                amount=parcel_value,
                type=TransactionType.expense,
                date=due,
                category_id=data.category_id,
                card_id=data.card_id,
                status=TransactionStatus.pending,
                observation=data.observation,
                installment_id=installment.id,
                installment_number=i,
                installments_total=data.installments_total,
                is_installment=True,
            )
            self.db.add(txn)
            if i == 1:
                created = txn
        self.db.commit()
        if created:
            self.db.refresh(created)
        return created

    def update(
        self, user_id: str, transaction_id: str, data: TransactionUpdate
    ) -> Transaction:
        txn = self.repo.get_for_user(user_id, transaction_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        payload = data.model_dump(exclude_unset=True)
        if "amount" in payload:
            payload["amount"] = money(payload["amount"])
        if payload.get("status") is not None:
            new_status = payload["status"]
            payload["paid_at"] = (
                payload.get("date") or txn.date
                if new_status in (TransactionStatus.paid, TransactionStatus.received)
                else None
            )
        if "category_id" in payload:
            self._validate_ownership(
                user_id, payload["category_id"], None, payload.get("card_id")
            )
        for field, value in payload.items():
            if field in ("category_id", "account_id", "card_id", "observation"):
                if value == "":
                    value = None
            setattr(txn, field, value)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def delete(self, user_id: str, transaction_id: str) -> None:
        txn = self.repo.get_for_user(user_id, transaction_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        if txn.installment_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Esta parcela pertence a uma compra parcelada. "
                    "Exclua o parcelamento completo em Compras parceladas."
                ),
            )
        self.db.delete(txn)
        self.db.commit()

    def pay(self, user_id: str, transaction_id: str) -> Transaction:
        txn = self.repo.get_for_user(user_id, transaction_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        if txn.type == TransactionType.expense and txn.card_id:
            raise HTTPException(
                status_code=400,
                detail="Pague a fatura do cartão para quitar compras no cartão",
            )
        txn.status = (
            TransactionStatus.received
            if txn.type == TransactionType.income
            else TransactionStatus.paid
        )
        txn.paid_at = date.today()
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def cancel(self, user_id: str, transaction_id: str) -> Transaction:
        txn = self.repo.get_for_user(user_id, transaction_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        txn.status = TransactionStatus.canceled
        txn.paid_at = None
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def transfer(self, user_id: str, data: TransferCreate) -> Transaction:
        from_acc = self._get_owned_account(user_id, data.from_account_id)
        to_acc = self._get_owned_account(user_id, data.to_account_id)
        if from_acc.id == to_acc.id:
            raise HTTPException(
                status_code=400, detail="As contas devem ser diferentes"
            )
        txn = Transaction(
            user_id=user_id,
            description=data.description.strip(),
            amount=money(data.amount),
            type=TransactionType.transfer,
            date=data.date,
            from_account_id=from_acc.id,
            to_account_id=to_acc.id,
            status=TransactionStatus.paid,
            observation=data.observation,
            paid_at=data.date,
        )
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn