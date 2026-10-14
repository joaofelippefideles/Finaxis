from fastapi import APIRouter, Depends, status
from app.database.session import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AuthPayload,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # O token é autodestrutível via expiração; o cliente apaga o token local.
    return None


@router.get("/me", response_model=AuthPayload)
def me(user: User = Depends(get_current_user)):
    settings = get_settings()
    return AuthPayload(
        id=user.id,
        email=user.email,
        name=user.name,
        currency=user.currency,
        date_format=user.date_format,
        locale=user.locale,
    )