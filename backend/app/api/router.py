from fastapi import APIRouter

from app.api.routes import (
    accounts,
    auth,
    budgets,
    cards,
    categories,
    dashboard,
    import_route,
    installments,
    notifications,
    payables,
    receivables,
    recurring,
    reports,
    search,
    settings,
    transactions,
    transfers,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(transactions.router)
api_router.include_router(transfers.router)
api_router.include_router(categories.router)
api_router.include_router(accounts.router)
api_router.include_router(cards.router)
api_router.include_router(installments.router)
api_router.include_router(budgets.router)
api_router.include_router(payables.router)
api_router.include_router(receivables.router)
api_router.include_router(recurring.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(import_route.router)
api_router.include_router(search.router)
api_router.include_router(settings.router)