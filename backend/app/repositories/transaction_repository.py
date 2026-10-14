from datetime import date
from decimal import Decimal
from typing import Optional

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository):
    def get_for_user(self, user_id: str, transaction_id: str) -> Transaction | None:
        txn = self.db.get(Transaction, transaction_id)
        if txn is None or txn.user_id != user_id:
            return None
        return txn

    def list_transactions(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ttype: Optional[TransactionType | str] = None,
        status: Optional[TransactionStatus | str] = None,
        category_id: Optional[str] = None,
        account_id: Optional[str] = None,
        card_id: Optional[str] = None,
        query: Optional[str] = None,
        order_by_desc: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Transaction]:
        rows = [t for t in self.db.all(Transaction) if t.user_id == user_id]
        if start_date:
            rows = [t for t in rows if t.date >= start_date]
        if end_date:
            rows = [t for t in rows if t.date <= end_date]
        if ttype is not None:
            wanted = TransactionType(ttype)
            rows = [t for t in rows if t.type == wanted]
        if status is not None:
            wanted = TransactionStatus(status)
            rows = [t for t in rows if t.status == wanted]
        if category_id:
            rows = [t for t in rows if t.category_id == category_id]
        if account_id:
            rows = [
                t
                for t in rows
                if account_id in (t.account_id, t.from_account_id, t.to_account_id)
            ]
        if card_id:
            rows = [t for t in rows if t.card_id == card_id]
        if query:
            needle = query.lower()
            rows = [
                t
                for t in rows
                if needle in (t.description or "").lower()
                or needle in (t.observation or "").lower()
            ]
        rows.sort(key=lambda t: (t.date, t.created_at), reverse=order_by_desc)
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def count(self, user_id: str, **filters) -> int:
        return len([t for t in self.db.all(Transaction) if t.user_id == user_id])

    def sum_by_type(
        self,
        user_id: str,
        ttype: TransactionType,
        statuses: list[TransactionStatus],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[str] = None,
    ) -> Decimal:
        total = Decimal("0")
        for txn in self.db.all(Transaction):
            if txn.user_id != user_id or txn.type != ttype:
                continue
            if txn.status not in statuses:
                continue
            if category_id and txn.category_id != category_id:
                continue
            if start_date and txn.date < start_date:
                continue
            if end_date and txn.date > end_date:
                continue
            total += txn.amount
        return total

    def group_by_category(self, user_id: str, start: date, end: date) -> list[dict]:
        grouped: dict[str, Decimal] = {}
        valid = (TransactionStatus.paid, TransactionStatus.received)
        for txn in self.db.all(Transaction):
            if txn.user_id != user_id or txn.type != TransactionType.expense:
                continue
            if txn.status not in valid:
                continue
            if not (start <= txn.date <= end):
                continue
            grouped[txn.category_id] = grouped.get(txn.category_id, Decimal("0")) + txn.amount
        rows = [{"category_id": cid, "amount": amount} for cid, amount in grouped.items()]
        rows.sort(key=lambda r: r["amount"], reverse=True)
        return rows