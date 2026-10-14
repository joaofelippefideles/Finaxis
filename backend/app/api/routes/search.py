from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_db
from app.database.session import Session
from app.models.category import Category
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.utils.money import parse_brl_amount
from app.utils.dates import parse_iso_or_br

router = APIRouter(prefix="/search", tags=["Busca"])


@router.get("")
def global_search(
    q: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    card_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[str] = None,
    max_amount: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_d = parse_iso_or_br(start_date) if start_date else None
    end_d = parse_iso_or_br(end_date) if end_date else None
    min_amount_d = parse_brl_amount(min_amount) if min_amount else None
    max_amount_d = parse_brl_amount(max_amount) if max_amount else None

    rows = [t for t in db.all(Transaction) if t.user_id == user.id]
    if q:
        needle = q.lower()
        rows = [
            t
            for t in rows
            if needle in (t.description or "").lower()
            or needle in (t.observation or "").lower()
        ]
    if type:
        wanted = TransactionType(type)
        rows = [t for t in rows if t.type == wanted]
    if status:
        wanted = TransactionStatus(status)
        rows = [t for t in rows if t.status == wanted]
    if category_id:
        rows = [t for t in rows if t.category_id == category_id]
    if account_id:
        rows = [t for t in rows if t.account_id == account_id]
    if card_id:
        rows = [t for t in rows if t.card_id == card_id]
    if start_d:
        rows = [t for t in rows if t.date >= start_d]
    if end_d:
        rows = [t for t in rows if t.date <= end_d]
    if min_amount_d is not None:
        rows = [t for t in rows if t.amount >= min_amount_d]
    if max_amount_d is not None:
        rows = [t for t in rows if t.amount <= max_amount_d]

    rows.sort(key=lambda t: t.date, reverse=True)
    total = len(rows)
    paged = rows[(page - 1) * page_size : (page - 1) * page_size + page_size]

    cat_names = {
        c.id: c.name for c in db.all(Category) if c.user_id == user.id
    }
    results = []
    for t in paged:
        results.append(
            {
                "id": t.id,
                "description": t.description,
                "amount": str(t.amount),
                "type": t.type.value,
                "status": t.status.value,
                "date": t.date.isoformat(),
                "category": cat_names.get(t.category_id),
                "category_id": t.category_id,
                "account_id": t.account_id,
                "card_id": t.card_id,
            }
        )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results,
    }