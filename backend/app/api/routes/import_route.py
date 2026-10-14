from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.misc import ImportResult
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["Importação"])


@router.post("/transactions", response_model=ImportResult)
async def import_transactions(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo muito grande (máx 5MB)")
    try:
        return ImportService(db).import_transactions(
            user.id, file.filename or "arquivo.csv", content
        )
    except HTTPException:
        raise