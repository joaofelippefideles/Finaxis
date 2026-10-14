from app.models.enums import ListItemStatus
from app.models.payable_receivable import Payable, Receivable
from app.repositories.base import BaseRepository


def _list_items(items, include_canceled):
    if include_canceled:
        return list(items)
    return [i for i in items if i.status != ListItemStatus.canceled]


class PayableRepository(BaseRepository):
    def list_for_user(self, user_id: str, include_canceled: bool = False) -> list[Payable]:
        return _list_items(self.list_all(Payable, user_id), include_canceled)


class ReceivableRepository(BaseRepository):
    def list_for_user(self, user_id: str, include_canceled: bool = False) -> list[Receivable]:
        return _list_items(self.list_all(Receivable, user_id), include_canceled)