from app.models.installment import Installment
from app.repositories.base import BaseRepository


class InstallmentRepository(BaseRepository):
    def list_for_user(self, user_id: str) -> list[Installment]:
        rows = self.list_all(Installment, user_id)
        rows.sort(key=lambda g: g.created_at, reverse=True)
        return rows

    def get_for_user(self, user_id: str, installments_id: str) -> Installment | None:
        group = self.db.get(Installment, installments_id)
        if group is None or group.user_id != user_id:
            return None
        return group