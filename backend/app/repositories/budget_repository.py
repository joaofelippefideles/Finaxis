from app.models.budget import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository):
    def get_by_user(self, user_id: str) -> list[Budget]:
        return self.list_all(Budget, user_id)

    def list_for_user(self, user_id: str, month: str | None = None) -> list[Budget]:
        rows = self.list_all(Budget, user_id)
        if month is not None:
            rows = [b for b in rows if b.month in (None, month)]
        return rows

    def find_existing(
        self, user_id: str, category_id: str, month: str | None
    ) -> Budget | None:
        for b in self.list_all(Budget, user_id):
            if b.category_id == category_id and b.month == month:
                return b
        return None