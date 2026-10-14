from typing import Optional

from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.enums import CategoryType
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    type: Optional[CategoryType] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).list(user.id, type)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).create(user.id, data)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).get(user.id, category_id)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: str,
    data: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).update(user.id, category_id, data)


@router.patch("/{category_id}/toggle", response_model=CategoryRead)
def toggle_category(
    category_id: str,
    active: bool,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).toggle(user.id, category_id, active)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CategoryService(db).delete(user.id, category_id)
    return None