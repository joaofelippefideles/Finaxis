from typing import Literal

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.payable_receivable import (
    ReceivableCreate,
    ReceivableRead,
    ReceivableUpdate,
)
from app.services.payable_receivable_service import ReceivableService

router = APIRouter(prefix="/receivables", tags=["Contas a receber"])


@router.get("", response_model=list[ReceivableRead])
def list_receivables(
    group: Literal["todas", "vencidos", "hoje", "proximos", "recebidos"] = "todas",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReceivableService(db).list(user.id, group)


@router.post("", response_model=ReceivableRead, status_code=status.HTTP_201_CREATED)
def create_receivable(
    data: ReceivableCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReceivableService(db).create(user.id, data)


@router.put("/{receivable_id}", response_model=ReceivableRead)
def update_receivable(
    receivable_id: str,
    data: ReceivableUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReceivableService(db).update(user.id, receivable_id, data)


@router.post("/{receivable_id}/receive", response_model=ReceivableRead)
def receive_receivable(
    receivable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReceivableService(db).receive(user.id, receivable_id)


@router.post("/{receivable_id}/cancel", response_model=ReceivableRead)
def cancel_receivable(
    receivable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReceivableService(db).cancel(user.id, receivable_id)


@router.delete("/{receivable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receivable(
    receivable_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ReceivableService(db).delete(user.id, receivable_id)
    return None