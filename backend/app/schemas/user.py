from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import AuthPayload
from app.schemas.category import CategoryRead
from app.schemas.account import AccountRead
from app.schemas.credit_card import CreditCardRead


class PreferencesUpdate(BaseModel):
    currency: str | None = None
    date_format: str | None = None
    locale: str | None = None


class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile: AuthPayload
    preferences: PreferencesUpdate | None = None
    default_categories: list[CategoryRead] = []
    accounts: list[AccountRead] = []
    cards: list[CreditCardRead] = []


class UserOverview(BaseModel):
    id: str
    name: str
    email: str
    currency: str
    date_format: str
    locale: str
    created_at: datetime