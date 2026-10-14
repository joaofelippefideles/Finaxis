from app.models.base import JsonModel

Base = JsonModel

from app.models import (  # noqa: E402,F401  (reexport por compatibilidade)
    Account,
    Budget,
    Category,
    CreditCard,
    Installment,
    Notification,
    Payable,
    Receivable,
    RecurringTransaction,
    Transaction,
    User,
)

__all__ = [
    "Base",
    "User",
    "Category",
    "Account",
    "CreditCard",
    "Installment",
    "Transaction",
    "RecurringTransaction",
    "Budget",
    "Payable",
    "Receivable",
    "Notification",
]