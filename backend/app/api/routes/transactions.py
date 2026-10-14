from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.enums import TransactionStatus, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Lançamentos"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    card_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txns = TransactionService(db).repo.list_transactions(
        user.id,
        start_date=start_date,
        end_date=end_date,
        ttype=type,
        status=status,
        category_id=category_id,
        account_id=account_id,
        card_id=card_id,
        query=search,
        limit=limit,
    )
    return txns


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).create(user.id, data)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = TransactionService(db).repo.get_for_user(user.id, transaction_id)
    if txn is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    return txn


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).update(user.id, transaction_id, data)


@router.post("/{transaction_id}/pay", response_model=TransactionRead)
def pay_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).pay(user.id, transaction_id)


@router.post("/{transaction_id}/cancel", response_model=TransactionRead)
def cancel_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).cancel(user.id, transaction_id)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    TransactionService(db).delete(user.id, transaction_id)
    return None