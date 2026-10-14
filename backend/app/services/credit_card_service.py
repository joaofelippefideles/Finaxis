import calendar
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.enums import CategoryType, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.credit_card_repository import CreditCardRepository
from app.schemas.credit_card import (
    CardInvoice,
    CardPaymentResult,
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
)
from app.utils.dates import add_months
from app.utils.money import money

INVOICE_CATEGORY_NAME = "Fatura de cartão"


def _clamp_day(year: int, month: int, day: int) -> int:
    last = calendar.monthrange(year, month)[1]
    return min(day, last)


def closing_date_on(card: CreditCard, year: int, month: int) -> date:
    return date(year, month, _clamp_day(year, month, card.closing_day))


def due_date_on(card: CreditCard, year: int, month: int) -> date:
    return date(year, month, _clamp_day(year, month, card.due_day))


def invoice_period(card: CreditCard, year: int, month: int) -> tuple[date, date]:
    """Fatura do mês: compras em (fechamento do mês anterior, fechamento deste mês]."""
    closing = closing_date_on(card, year, month)
    prev = closing_date_on(card, *_ym(add_months(closing, -1)))
    return prev, closing


class CreditCardService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CreditCardRepository(db)
        self.category_repo = CategoryRepository(db)

    def _get(self, user_id: str, card_id: str) -> CreditCard:
        card = self.repo.get_or_404(CreditCard, card_id)
        if card.user_id != user_id:
            raise HTTPException(status_code=404, detail="Cartão não encontrado")
        return card

    def list(self, user_id: str) -> list[CreditCardRead]:
        cards = self.repo.get_by_user(user_id)
        result = []
        for card in cards:
            if card.status.value == "cancelado":
                continue
            result.append(self.to_read(card))
        return result

    def to_read(self, card: CreditCard) -> CreditCardRead:
        used = self.repo.used_limit(card)
        today = date.today()
        last_close = closing_date_on(card, today.year, today.month)
        if last_close > today:
            last_close = closing_date_on(card, *_ym(add_months(today, -1)))
        prev_close = closing_date_on(card, *_ym(add_months(last_close, -1)))
        next_close = closing_date_on(card, *_ym(add_months(last_close, 1)))

        current = self._sum_pending_in(card, prev_close, last_close)
        nxt = self._sum_pending_in(card, last_close, next_close)
        return CreditCardRead(
            id=card.id,
            user_id=card.user_id,
            name=card.name,
            bank=card.bank,
            limit_amount=card.limit_amount,
            closing_day=card.closing_day,
            due_day=card.due_day,
            account_id=card.account_id,
            status=card.status,
            used_limit=used,
            available_limit=money(card.limit_amount - used),
            current_invoice=current,
            next_invoice=nxt,
        )

    def _sum_pending_in(self, card: CreditCard, start: date, end: date) -> Decimal:
        txns = self.repo.transactions_on_period(card.user_id, card.id, start, end)
        return money(sum((t.amount for t in txns), Decimal("0")))

    def get(self, user_id: str, card_id: str) -> CreditCardRead:
        return self.to_read(self._get(user_id, card_id))

    def create(self, user_id: str, data: CreditCardCreate) -> CreditCardRead:
        if data.account_id:
            acc = self.db.get(Account, data.account_id)
            if acc is None or acc.user_id != user_id:
                raise HTTPException(status_code=400, detail="Conta vinculada inválida")
        card = CreditCard(
            user_id=user_id,
            name=data.name.strip(),
            bank=data.bank,
            limit_amount=money(data.limit_amount),
            closing_day=data.closing_day,
            due_day=data.due_day,
            account_id=data.account_id,
            status=data.status,
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return self.to_read(card)

    def update(self, user_id: str, card_id: str, data: CreditCardUpdate) -> CreditCardRead:
        card = self._get(user_id, card_id)
        payload = data.model_dump(exclude_unset=True)
        if "limit_amount" in payload:
            payload["limit_amount"] = money(payload["limit_amount"])
        if "account_id" in payload and payload["account_id"]:
            acc = self.db.get(Account, payload["account_id"])
            if acc is None or acc.user_id != user_id:
                raise HTTPException(status_code=400, detail="Conta vinculada inválida")
        for field, value in payload.items():
            setattr(card, field, value)
        self.db.commit()
        self.db.refresh(card)
        return self.to_read(card)

    def delete(self, user_id: str, card_id: str) -> None:
        card = self._get(user_id, card_id)
        self.db.delete(card)
        self.db.commit()

    def invoices(self, user_id: str, card_id: str) -> list[CardInvoice]:
        card = self._get(user_id, card_id)
        today = date.today()
        last_close = closing_date_on(card, today.year, today.month)
        if last_close > today:
            last_close = closing_date_on(card, *_ym(add_months(today, -1)))
        periods = []
        for i in range(5, -1, -1):
            month_anchor = add_months(last_close, -i)
            y, m = _ym(month_anchor)
            start, end = invoice_period(card, y, m)
            txns = self.repo.transactions_on_period(card.user_id, card.id, start, end)
            pending = [t for t in txns if t.status == TransactionStatus.pending]
            total = money(sum((t.amount for t in pending), Decimal("0")))
            periods.append(
                CardInvoice(
                    month=f"{y:04d}-{m:02d}",
                    due_date=due_date_on(card, y, m).isoformat(),
                    total=total,
                    items=[self._serialize_txn(t) for t in pending],
                )
            )
        return periods

    @staticmethod
    def _serialize_txn(txn: Transaction) -> dict:
        return {
            "id": txn.id,
            "description": txn.description,
            "amount": str(txn.amount),
            "date": txn.date.isoformat(),
            "installment_number": txn.installment_number,
            "installments_total": txn.installments_total,
        }

    def pay_invoice(self, user_id: str, card_id: str, month: str) -> CardPaymentResult:
        card = self._get(user_id, card_id)
        try:
            year, m = (int(x) for x in month.split("-"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Mês inválido")
        if m < 1 or m > 12:
            raise HTTPException(status_code=400, detail="Mês inválido")

        start, end = invoice_period(card, year, m)
        txns = [
            t
            for t in self.repo.transactions_on_period(card.user_id, card.id, start, end)
            if t.status == TransactionStatus.pending
        ]
        if not txns:
            raise HTTPException(
                status_code=400,
                detail="Não há lançamentos pendentes nesta fatura",
            )
        if card.account_id is None:
            raise HTTPException(
                status_code=400,
                detail="Cadastre uma conta vinculada ao cartão para pagar a fatura",
            )
        acc = self.db.get(Account, card.account_id)
        if acc is None or acc.user_id != user_id:
            raise HTTPException(status_code=400, detail="Conta vinculada inválida")

        total = money(sum((t.amount for t in txns), Decimal("0")))
        cat = self.category_repo.find_by_name(
            user_id, INVOICE_CATEGORY_NAME, CategoryType.expense
        )
        if cat is None:
            cat = Category(
                user_id=user_id,
                name=INVOICE_CATEGORY_NAME,
                type=CategoryType.expense,
                is_default=True,
                active=True,
            )
            self.db.add(cat)
            self.db.flush()

        due = due_date_on(card, year, m)
        invoice_txn = Transaction(
            user_id=user_id,
            description=f"Pagamento de fatura - {card.name}",
            amount=total,
            type=TransactionType.expense,
            date=due,
            category_id=cat.id,
            account_id=acc.id,
            status=TransactionStatus.paid,
            paid_at=due,
        )
        self.db.add(invoice_txn)
        for t in txns:
            t.status = TransactionStatus.paid
            t.paid_at = due
        self.db.commit()
        return CardPaymentResult(
            invoice=month,
            paid_total=total,
            transactions=[t.id for t in txns],
        )


def _ym(d: date) -> tuple[int, int]:
    return d.year, d.month