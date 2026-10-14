from fastapi import HTTPException, status

from app.database.session import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import CategoryType
from app.models.payable_receivable import Payable, Receivable
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def list(self, user_id: str, ctype: CategoryType | None = None) -> list[CategoryRead]:
        if ctype:
            cats = self.repo.get_type(user_id, ctype)
        else:
            cats = self.repo.get_by_user(user_id)
        return [
            CategoryRead.model_validate(c)
            for c in sorted(cats, key=lambda c: (c.type.value, c.name))
        ]

    def get(self, user_id: str, category_id: str) -> CategoryRead:
        cat = self.repo.get_or_404(Category, category_id)
        if cat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        return CategoryRead.model_validate(cat)

    def create(self, user_id: str, data: CategoryCreate) -> CategoryRead:
        existing = self.repo.find_by_name(user_id, data.name, data.type)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="Já existe uma categoria com esse nome",
            )
        cat = Category(
            user_id=user_id,
            name=data.name,
            type=data.type,
            color=data.color,
            icon=data.icon,
            is_default=False,
            active=True,
        )
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return CategoryRead.model_validate(cat)

    def update(self, user_id: str, category_id: str, data: CategoryUpdate) -> CategoryRead:
        cat = self.repo.get_or_404(Category, category_id)
        if cat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"]:
            existing = self.db.find(
                Category, user_id=user_id, name=payload["name"]
            )
            if existing and existing.id != category_id:
                raise HTTPException(status_code=409, detail="Nome já em uso")
        for field, value in payload.items():
            setattr(cat, field, value)
        self.db.commit()
        self.db.refresh(cat)
        return CategoryRead.model_validate(cat)

    def delete(self, user_id: str, category_id: str) -> None:
        cat = self.repo.get_or_404(Category, category_id)
        if cat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        if cat.is_default:
            raise HTTPException(
                status_code=400,
                detail="Categorias padrão não podem ser excluídas; desative-as",
            )
        references = (
            sum(
                1
                for t in self.db.all(Transaction)
                if t.user_id == user_id and t.category_id == category_id
            )
            + sum(
                1
                for b in self.db.all(Budget)
                if b.user_id == user_id and b.category_id == category_id
            )
            + sum(
                1
                for p in self.db.all(Payable)
                if p.user_id == user_id and p.category_id == category_id
            )
            + sum(
                1
                for r in self.db.all(Receivable)
                if r.user_id == user_id and r.category_id == category_id
            )
        )
        if references:
            cat.active = False
            self.db.commit()
            return
        self.db.delete(cat)
        self.db.commit()

    def toggle(self, user_id: str, category_id: str, active: bool) -> CategoryRead:
        cat = self.repo.get_or_404(Category, category_id)
        if cat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        cat.active = active
        self.db.commit()
        self.db.refresh(cat)
        return CategoryRead.model_validate(cat)