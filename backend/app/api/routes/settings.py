from fastapi import APIRouter, Depends
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, AuthPayload
from app.schemas.user import PreferencesUpdate, ProfileUpdate, UserSettings
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["Configurações"])


@router.get("", response_model=UserSettings)
def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SettingsService(db).get(user)


@router.put("/profile", response_model=AuthPayload)
def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SettingsService(db).update_profile(user, data)


@router.put("/preferences")
def update_preferences(
    data: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SettingsService(db).update_preferences(user, data)


@router.put("/password")
def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    SettingsService(db).change_password(user, data)
    return {"message": "Senha alterada com sucesso"}