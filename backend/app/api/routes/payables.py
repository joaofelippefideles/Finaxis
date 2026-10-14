from typing import Literal

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.enums import ListItemStatus
from app.models.user import User
from app.schemas.payable_receivable import (
    PayableCreate,
    PayableRead,
    PayableUpdate,
)
from app.services.payable_receivable_service import PayableService

router = APIRouter(prefix="/payables", tags=["Contas a pagar"])


@router.get("", response_model=list[PayableRead])
def list_payables(
    group: Literal["todas", "vencidas", "hoje", "proximas", "pagas"] = "todas",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PayableService(db).list(user.id, group)


@router.post("", response_model=PayableRead, status_code=status.HTTP_201_CREATED)
def create_payable(
    data: PayableCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PayableService(db).create(user.id, data)


@router.put("/{payable_id}", response_model=PayableRead)
def update_payable(
    payable_id: str,
    data: PayableUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PayableService(db).update(user.id, payable_id, data)


@router.post("/{payable_id}/pay", response_model=PayableRead)
def pay_payable(
    payable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PayableService(db).pay(user.id, payable_id)


@router.post("/{payable_id}/cancel", response_model=PayableRead)
def cancel_payable(
    payable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PayableService(db).cancel(user.id, payable_id)


@router.post("/{payable_id}/reopen", response_model=PayableRead)
def reopen_payable(
    payable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = PayableService(db)._get_owned(user.id, payable_id)
    item.status = ListItemStatus.pending
    item.paid_at = None
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{payable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payable(
    payable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PayableService(db).delete(user.id, payable_id)
    return None