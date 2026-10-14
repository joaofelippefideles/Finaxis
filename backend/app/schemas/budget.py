from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import RecurrenceFrequency
from app.schemas.account import validate_money


class BudgetCreate(BaseModel):
    category_id: str
    limit_amount: Decimal = Field(gt=0)
    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")

    @field_validator("limit_amount")
    @classmethod
    def clean_limit(cls, v: Decimal) -> Decimal:
        return validate_money(v)


class BudgetUpdate(BaseModel):
    limit_amount: Optional[Decimal] = Field(default=None, gt=0)
    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")

    @field_validator("limit_amount")
    @classmethod
    def clean_limit(cls, v: Decimal | None) -> Decimal | None:
        return validate_money(v) if v is not None else v


class BudgetUsage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    category_name: str
    month: Optional[str] = None
    limit_amount: Decimal
    spent: Decimal = Decimal("0")
    remaining: Decimal = Decimal("0")
    percent: Decimal = Decimal("0")
    level: str = "ok"  # ok | warn | critical


class BudgetSummary(BaseModel):
    month: str
    total_limit: Decimal = Decimal("0")
    total_spent: Decimal = Decimal("0")
    items: list[BudgetUsage] = []