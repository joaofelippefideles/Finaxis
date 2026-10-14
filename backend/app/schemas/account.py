from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AccountType


def validate_money(v: Decimal) -> Decimal:
    if v < 0:
        raise ValueError("O valor não pode ser negativo")
    return v.quantize(Decimal("0.01"))


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    bank: Optional[str] = Field(default=None, max_length=80)
    type: AccountType = AccountType.checking
    initial_balance: Decimal = Field(default=Decimal("0"))
    agency: Optional[str] = Field(default=None, max_length=20)
    account_number: Optional[str] = Field(default=None, max_length=30)
    active: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("initial_balance")
    @classmethod
    def clean_balance(cls, v: Decimal) -> Decimal:
        return validate_money(v)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    bank: Optional[str] = Field(default=None, max_length=80)
    type: Optional[AccountType] = None
    initial_balance: Optional[Decimal] = None
    agency: Optional[str] = Field(default=None, max_length=20)
    account_number: Optional[str] = Field(default=None, max_length=30)
    active: Optional[bool] = None

    @field_validator("initial_balance")
    @classmethod
    def clean_balance(cls, v: Decimal | None) -> Decimal | None:
        return validate_money(v) if v is not None else v


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    balance: Decimal = Decimal("0")