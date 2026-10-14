from datetime import date, datetime, timedelta
from typing import Optional

import calendar


def add_months(d: date, months: int) -> date:
    """Adiciona meses a uma data mantendo o dia (limitado ao último dia do mês)."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def next_occurrence(d: date, frequency: str) -> date:
    if frequency == "diario":
        return d + timedelta(days=1)
    if frequency == "semanal":
        return d + timedelta(days=7)
    if frequency == "mensal":
        return add_months(d, 1)
    if frequency == "anual":
        return add_months(d, 12)
    raise ValueError(f"Frequência inválida: {frequency}")


def month_range(year: int, month: int) -> tuple[date, date]:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def today_local() -> date:
    return datetime.now().date()


def fmt_date_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def parse_iso_or_br(value: str) -> Optional[date]:
    value = value.strip()
    try:
        if "-" in value:
            return date.fromisoformat(value)
        parts = value.split("/")
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, TypeError):
        return None
    return None