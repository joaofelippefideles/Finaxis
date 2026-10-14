from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status

from app.database.session import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.budget_repository import BudgetRepository
from app.schemas.budget import BudgetCreate, BudgetSummary, BudgetUpdate, BudgetUsage
from app.utils.dates import month_key
from app.utils.money import money


class BudgetService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BudgetRepository(db)

    def _owns_category(self, user_id: str, category_id: str) -> bool:
        cat = self.db.get(Category, category_id)
        return cat is not None and cat.user_id == user_id

    def create(self, user_id: str, data: BudgetCreate) -> BudgetUsage:
        if not self._owns_category(user_id, data.category_id):
            raise HTTPException(status_code=400, detail="Categoria inválida")
        existing = self.repo.find_existing(user_id, data.category_id, data.month)
        if existing is not None:
            raise HTTPException(
                status_code=409, detail="Já existe orçamento para esta categoria"
            )
        budget = Budget(
            user_id=user_id,
            category_id=data.category_id,
            limit_amount=money(data.limit_amount),
            month=data.month,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return self.build_usage(user_id, budget, data.month or month_key(date.today()))

    def list(self, user_id: str, month: str | None = None) -> BudgetSummary:
        month = month or month_key(date.today())
        budgets = self.repo.list_for_user(user_id, month)
        items = [self.build_usage(user_id, b, month) for b in budgets]
        total_limit = money(sum((b.limit_amount for b in budgets), Decimal("0")))
        total_spent = money(sum((i.spent for i in items), Decimal("0")))
        return BudgetSummary(
            month=month, total_limit=total_limit, total_spent=total_spent, items=items
        )

    def build_usage(self, user_id: str, budget: Budget, month: str) -> BudgetUsage:
        year, month_num = (int(x) for x in month.split("-"))
        start = date(year, month_num, 1)
        if month_num == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month_num + 1, 1) - timedelta(days=1)  # último dia
        spent = money(
            sum(
                (
                    t.amount
                    for t in self.db.all(Transaction)
                    if t.user_id == user_id
                    and t.category_id == budget.category_id
                    and t.type == TransactionType.expense
                    and t.status != TransactionStatus.canceled
                    and start <= t.date <= end
                ),
                Decimal("0"),
            )
        )
        limit = money(budget.limit_amount)
        remaining = money(limit - spent)
        percent = money((spent / limit * 100)) if limit > 0 else Decimal("0")
        cat = self.db.get(Category, budget.category_id)
        level = "ok"
        if percent >= Decimal("100"):
            level = "critical"
        elif percent >= Decimal("90"):
            level = "critical"
        elif percent >= Decimal("80"):
            level = "warn"
        return BudgetUsage(
            id=budget.id,
            category_id=budget.category_id,
            category_name=cat.name if cat else "?",
            month=budget.month,
            limit_amount=limit,
            spent=spent,
            remaining=remaining,
            percent=percent,
            level=level,
        )

    def update(self, user_id: str, budget_id: str, data: BudgetUpdate) -> BudgetUsage:
        budget = self.repo.get_or_404(Budget, budget_id)
        if budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Orçamento não encontrado")
        payload = data.model_dump(exclude_unset=True)
        if "limit_amount" in payload:
            payload["limit_amount"] = money(payload["limit_amount"])
        for field, value in payload.items():
            setattr(budget, field, value)
        self.db.commit()
        self.db.refresh(budget)
        return self.build_usage(user_id, budget, budget.month or month_key(date.today()))

    def delete(self, user_id: str, budget_id: str) -> None:
        budget = self.repo.get_or_404(Budget, budget_id)
        if budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Orçamento não encontrado")
        self.db.delete(budget)
        self.db.commit()