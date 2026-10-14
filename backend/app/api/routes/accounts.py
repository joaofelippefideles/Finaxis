from typing import Optional

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Contas"])


@router.get("", response_model=list[AccountRead])
def list_accounts(
    include_inactive: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).list(user.id, include_inactive=include_inactive)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).create(user.id, data)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).get(user.id, account_id)


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: str,
    data: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).update(user.id, account_id, data)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AccountService(db).delete(user.id, account_id)
    return None