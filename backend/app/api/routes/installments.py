from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.installment import InstallmentCreate, InstallmentRead
from app.services.installment_service import InstallmentService

router = APIRouter(prefix="/installments", tags=["Compras parceladas"])


@router.get("", response_model=list[InstallmentRead])
def list_installments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return InstallmentService(db).list(user.id)


@router.post("", response_model=InstallmentRead, status_code=status.HTTP_201_CREATED)
def create_installment(
    data: InstallmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return InstallmentService(db).create(user.id, data)


@router.get("/{installments_id}", response_model=InstallmentRead)
def get_installment(
    installments_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return InstallmentService(db).get(user.id, installments_id)


@router.delete("/{installments_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment(
    installments_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    InstallmentService(db).delete(user.id, installments_id)
    return None