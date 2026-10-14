from decimal import Decimal

from app.models.account import Account
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    def get_by_user(self, user_id: str) -> list[Account]:
        return self.list_all(Account, user_id)

    def balance(self, account: Account) -> Decimal:
        """Calcula o saldo atual de uma conta a partir das movimentações."""
        user_id = account.user_id
        account_id = account.id
        initial = Decimal(account.initial_balance or 0)

        income = Decimal("0")
        expense = Decimal("0")
        transfer_in = Decimal("0")
        transfer_out = Decimal("0")

        for txn in self.db.all(Transaction):
            if txn.user_id != user_id:
                continue
            if (
                txn.account_id == account_id
                and txn.type == TransactionType.income
                and txn.status in (TransactionStatus.received, TransactionStatus.paid)
            ):
                income += txn.amount
            elif (
                txn.account_id == account_id
                and txn.type == TransactionType.expense
                and txn.status in (TransactionStatus.paid, TransactionStatus.received)
            ):
                expense += txn.amount
            if txn.to_account_id == account_id and txn.status != TransactionStatus.canceled:
                transfer_in += txn.amount
            if txn.from_account_id == account_id and txn.status != TransactionStatus.canceled:
                transfer_out += txn.amount

        return initial + income + transfer_in - expense - transfer_out