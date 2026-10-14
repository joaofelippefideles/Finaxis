from datetime import date
from decimal import Decimal

from app.models.credit_card import CreditCard
from app.models.enums import TransactionStatus
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class CreditCardRepository(BaseRepository):
    def get_by_user(self, user_id: str) -> list[CreditCard]:
        return self.list_all(CreditCard, user_id)

    def used_limit(self, card: CreditCard) -> Decimal:
        total = Decimal("0")
        for txn in self.db.all(Transaction):
            if (
                txn.user_id == card.user_id
                and txn.card_id == card.id
                and txn.status == TransactionStatus.pending
            ):
                total += txn.amount
        return total

    def transactions_on_period(
        self, user_id: str, card_id: str, start: date, end: date
    ) -> list[Transaction]:
        rows = [
            t
            for t in self.db.all(Transaction)
            if t.user_id == user_id
            and t.card_id == card_id
            and start <= t.date <= end
        ]
        rows.sort(key=lambda t: t.date)
        return rows