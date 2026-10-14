from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def list_for_user(self, user_id: str, limit: int = 50) -> list[Notification]:
        rows = self.list_all(Notification, user_id)
        rows.sort(key=lambda n: n.created_at, reverse=True)
        return rows[:limit]

    def unread_count(self, user_id: str) -> int:
        return len(
            [n for n in self.list_all(Notification, user_id) if not n.is_read]
        )

    def mark_all_read(self, user_id: str) -> None:
        for notification in self.list_all(Notification, user_id):
            notification.is_read = True
        self.commit()