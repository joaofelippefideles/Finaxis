from fastapi import HTTPException, status

from app.database.session import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.auth import (
    AuthPayload,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)

    def _find_by_email(self, email: str) -> User | None:
        return self.db.find(User, email=email.lower())

    def register(self, data: RegisterRequest) -> TokenResponse:
        email = data.email.lower()
        if self._find_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado",
            )
        user = User(
            name=data.name.strip(),
            email=email,
            password_hash=hash_password(data.password),
        )
        self.db.add(user)
        self.db.flush()
        self.category_repo.seed_defaults(user.id)
        self.db.commit()
        self.db.refresh(user)
        return self._build_token(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self._find_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )
        return self._build_token(user)

    def _build_token(self, user: User) -> TokenResponse:
        settings = get_settings()
        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=AuthPayload(
                id=user.id,
                email=user.email,
                name=user.name,
                currency=user.currency,
                date_format=user.date_format,
                locale=user.locale,
            ),
        )

    def payload(self, user: User) -> AuthPayload:
        return AuthPayload(
            id=user.id,
            email=user.email,
            name=user.name,
            currency=user.currency,
            date_format=user.date_format,
            locale=user.locale,
        )