from app.models.enums import RecurrenceStatus
from app.models.recurring import RecurringTransaction
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class RecurringRepository(BaseRepository):
    def list_for_user(self, user_id: str) -> list[RecurringTransaction]:
        return self.list_all(RecurringTransaction, user_id)

    def active_records(self, user_id: str) -> list[RecurringTransaction]:
        rows = [
            r
            for r in self.list_all(RecurringTransaction, user_id)
            if r.status == RecurrenceStatus.active
        ]
        rows.sort(key=lambda r: r.next_due_date)
        return rows

    def generated_count(self, user_id: str, recurring_id: str) -> int:
        return sum(
            1
            for t in self.db.all(Transaction)
            if t.user_id == user_id and t.recurring_id == recurring_id
        )