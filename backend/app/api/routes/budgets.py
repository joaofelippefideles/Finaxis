from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetSummary, BudgetUpdate, BudgetUsage
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Orçamento"])


@router.get("", response_model=BudgetSummary)
def list_budgets(
    month: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).list(user.id, month)


@router.post("", response_model=BudgetUsage, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).create(user.id, data)


@router.put("/{budget_id}", response_model=BudgetUsage)
def update_budget(
    budget_id: str,
    data: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update(user.id, budget_id, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    BudgetService(db).delete(user.id, budget_id)
    return None