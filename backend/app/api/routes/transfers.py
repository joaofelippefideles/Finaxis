from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.transaction import TransferCreate, TransactionRead
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transfers", tags=["Transferências"])


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transfer(
    data: TransferCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).transfer(user.id, data)