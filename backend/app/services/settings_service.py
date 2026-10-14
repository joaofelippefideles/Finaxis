from fastapi import HTTPException, status
from app.database.session import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, AuthPayload
from app.schemas.user import PreferencesUpdate, ProfileUpdate, UserSettings
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.account_service import AccountService
from app.services.credit_card_service import CreditCardService


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
        self.category_service = CategoryService(db)
        self.account_service = AccountService(db)
        self.card_service = CreditCardService(db)

    def get(self, user: User) -> UserSettings:
        categories = [
            c for c in self.category_service.list(user.id) if c.is_default
        ]
        return UserSettings(
            profile=self.auth_service.payload(user),
            preferences=PreferencesUpdate(
                currency=user.currency,
                date_format=user.date_format,
                locale=user.locale,
            ),
            default_categories=categories,
            accounts=self.account_service.list(user.id),
            cards=self.card_service.list(user.id),
        )

    def update_profile(self, user: User, data: ProfileUpdate) -> AuthPayload:
        payload = data.model_dump(exclude_unset=True)
        if "email" in payload:
            new_email = payload["email"].lower()
            existing = self.db.find(User, email=new_email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=409, detail="E-mail já cadastrado"
                )
            user.email = new_email
        if "name" in payload and payload["name"]:
            user.name = payload["name"].strip()
        self.db.commit()
        self.db.refresh(user)
        return self.auth_service.payload(user)

    def update_preferences(self, user: User, data: PreferencesUpdate) -> dict:
        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            if value:
                setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return {
            "currency": user.currency,
            "date_format": user.date_format,
            "locale": user.locale,
        }

    def change_password(self, user: User, data: ChangePasswordRequest) -> None:
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=400, detail="Senha atual incorreta"
            )
        user.password_hash = hash_password(data.new_password)
        self.db.commit()