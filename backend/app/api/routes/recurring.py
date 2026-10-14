from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.recurring import RecurringCreate, RecurringRead, RecurringUpdate
from app.services.recurring_service import RecurringService

router = APIRouter(prefix="/recurring", tags=["Lançamentos recorrentes"])


@router.get("", response_model=list[RecurringRead])
def list_recurring(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecurringService(db).list(user.id)


@router.post("", response_model=RecurringRead, status_code=status.HTTP_201_CREATED)
def create_recurring(
    data: RecurringCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecurringService(db).create(user.id, data)


@router.get("/{recurring_id}", response_model=RecurringRead)
def get_recurring(
    recurring_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecurringService(db).get(user.id, recurring_id)


@router.put("/{recurring_id}", response_model=RecurringRead)
def update_recurring(
    recurring_id: str,
    data: RecurringUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecurringService(db).update(user.id, recurring_id, data)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring(
    recurring_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    RecurringService(db).delete(user.id, recurring_id)
    return None


@router.post("/process", status_code=status.HTTP_200_OK)
def process_recurring(
    until: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    created = RecurringService(db).process(user.id, until)
    return {"generated": len(created)}