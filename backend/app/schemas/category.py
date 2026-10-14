from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CategoryType


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: CategoryType
    color: Optional[str] = Field(default=None, max_length=9)
    icon: Optional[str] = Field(default=None, max_length=40)


class CategoryCreate(CategoryBase):
    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip().title()


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    type: Optional[CategoryType] = None
    color: Optional[str] = Field(default=None, max_length=9)
    icon: Optional[str] = Field(default=None, max_length=40)
    active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        if v is None:
            return v
        return v.strip().title()


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    is_default: bool
    active: bool