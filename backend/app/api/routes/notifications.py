from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationCount, NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notificações"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).list(user.id, limit)


@router.get("/unread-count", response_model=NotificationCount)
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationCount(unread=NotificationService(db).unread_count(user.id))


@router.post("/generate")
def generate(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    created = NotificationService(db).generate(user.id)
    return {"generated": created}


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).mark_read(user.id, notification_id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    NotificationService(db).mark_all_read(user.id)
    return None