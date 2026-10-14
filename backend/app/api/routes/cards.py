from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.credit_card import (
    CardInvoice,
    CardPaymentResult,
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
)
from app.services.credit_card_service import CreditCardService

router = APIRouter(prefix="/cards", tags=["Cartões de crédito"])


@router.get("", response_model=list[CreditCardRead])
def list_cards(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).list(user.id)


@router.post("", response_model=CreditCardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    data: CreditCardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).create(user.id, data)


@router.get("/{card_id}", response_model=CreditCardRead)
def get_card(
    card_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).get(user.id, card_id)


@router.put("/{card_id}", response_model=CreditCardRead)
def update_card(
    card_id: str,
    data: CreditCardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).update(user.id, card_id, data)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CreditCardService(db).delete(user.id, card_id)
    return None


@router.get("/{card_id}/invoices", response_model=list[CardInvoice])
def list_invoices(
    card_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).invoices(user.id, card_id)


@router.post("/{card_id}/invoices/{month}/pay", response_model=CardPaymentResult)
def pay_invoice(
    card_id: str,
    month: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CreditCardService(db).pay_invoice(user.id, card_id, month)