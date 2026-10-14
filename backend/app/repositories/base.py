from typing import Any, Optional, Type, TypeVar

from fastapi import HTTPException, status

from app.models.base import JsonModel

ModelT = TypeVar("ModelT", bound=JsonModel)


class BaseRepository:
    def __init__(self, db):
        self.db = db

    def get(self, model: Type[ModelT], id: str) -> Optional[ModelT]:
        return self.db.get(model, id)

    def get_or_404(self, model: Type[ModelT], id: str) -> ModelT:
        obj = self.db.get(model, id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} não encontrado",
            )
        return obj

    def list_all(self, model: Type[ModelT], user_id: Optional[str] = None) -> list[ModelT]:
        items = self.db.all(model)
        if user_id is not None:
            items = [obj for obj in items if getattr(obj, "user_id", None) == user_id]
        return items

    def user_owned_or_404(self, model: Type[ModelT], id: str, user_id: str) -> ModelT:
        obj = self.get_or_404(model, id)
        if getattr(obj, "user_id", None) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro não encontrado",
            )
        return obj

    def add(self, obj: Any) -> Any:
        self.db.add(obj)
        return obj

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj: Any) -> Any:
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Any) -> None:
        self.db.delete(obj)