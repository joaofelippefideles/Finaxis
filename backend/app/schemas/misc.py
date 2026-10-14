from typing import Optional

from pydantic import BaseModel


class ImportResult(BaseModel):
    total: int = 0
    imported: int = 0
    errors: list[str] = []


class SearchFilters(BaseModel):
    q: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_amount: Optional[str] = None
    max_amount: Optional[str] = None
    page: int = 1
    page_size: int = 25