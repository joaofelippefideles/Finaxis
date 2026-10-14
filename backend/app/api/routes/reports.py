from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from app.database.session import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.report import ReportData, ReportQuery
from app.services.export_service import export_report
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Relatórios"])

CONTENT_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def _build_query(data: ReportQuery, start_date, end_date, **filters) -> ReportQuery:
    if data is not None:
        return data
    if not start_date or not end_date:
        raise HTTPException(
            status_code=400,
            detail="Informe start_date e end_date",
        )
    return ReportQuery(start_date=start_date, end_date=end_date, **filters)


def _filters_from_params(
    category_id, account_id, card_id, type, status
) -> dict:
    return {
        "category_id": category_id,
        "account_id": account_id,
        "card_id": card_id,
        "type": type,
        "status": status,
    }


@router.get("/summary", response_model=ReportData)
def report_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    card_id: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_query(
        None, start_date, end_date,
        **_filters_from_params(category_id, account_id, card_id, type, status),
    )
    try:
        return ReportService(db).build(user.id, query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/summary", response_model=ReportData)
def report_summary_post(
    data: ReportQuery,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return ReportService(db).build(user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/export")
def export(
    fmt: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[str] = None,
    account_id: Optional[str] = None,
    card_id: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_query(
        None, start_date, end_date,
        **_filters_from_params(category_id, account_id, card_id, type, status),
    )
    report = ReportService(db).build(user.id, query)
    content = export_report(report, fmt)
    filename = f"relatorio-{start_date or 'inicio'}-{end_date or 'fim'}.{fmt}"
    return Response(
        content=content,
        media_type=CONTENT_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )