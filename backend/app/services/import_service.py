from datetime import date, datetime

from fastapi import HTTPException
from app.database.session import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import (
    CategoryType,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.misc import ImportResult
from app.utils.csv_utils import (
    parse_csv_bytes,
    standardize_status,
    standardize_type,
)
from app.utils.dates import parse_iso_or_br
from app.utils.money import parse_brl_amount


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)

    def import_transactions(self, user_id: str, filename: str, content: bytes) -> ImportResult:
        try:
            rows = parse_csv_bytes(content)
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=f"Arquivo CSV inválido: {exc}")

        if not rows:
            raise HTTPException(status_code=400, detail="Arquivo vazio ou sem cabeçalhos reconhecidos")

        result = ImportResult(total=len(rows))
        accounts = {a.name.lower(): a for a in self.account_repo.get_by_user(user_id)}
        categories = {c.name.lower(): c for c in self.category_repo.get_by_user(user_id)}

        for idx, row in enumerate(rows, start=2):
            try:
                self._process_row(user_id, row, accounts, categories, result)
            except (KeyError, ValueError) as exc:
                result.errors.append(f"Linha {idx}: {exc}")

        self.db.commit()
        return result

    def _process_row(self, user_id, row, accounts, categories, result) -> None:
        description = (row.get("description") or row.get("descricao") or "").strip()
        if not description:
            raise ValueError("descrição vazia")

        amount_raw = row.get("amount") or row.get("valor") or ""
        if not amount_raw:
            raise ValueError("valor vazio")
        amount = parse_brl_amount(amount_raw)

        type_raw = row.get("type") or row.get("tipo") or ""
        txn_type = standardize_type(type_raw)
        if txn_type is None:
            raise ValueError(f"tipo inválido: '{type_raw}'")

        date_raw = row.get("date") or row.get("data") or ""
        d = parse_iso_or_br(date_raw)
        if d is None:
            raise ValueError(f"data inválida: '{date_raw}'")

        if txn_type == "transfer":
            raise ValueError("transações de transferência devem ser criadas no sistema")

        status_raw = row.get("status") or ""
        status = standardize_status(status_raw) or "pending"
        status_value = TransactionStatus(status)

        category_name = (row.get("category") or row.get("categoria") or "").strip()
        category_id = None
        if category_name:
            if category_name not in categories:
                ctype = (
                    CategoryType.income
                    if txn_type == "income"
                    else CategoryType.expense
                )
                cat = Category(
                    user_id=user_id,
                    name=category_name.title(),
                    type=ctype,
                    is_default=False,
                    active=True,
                )
                self.db.add(cat)
                self.db.flush()
                categories[category_name] = cat
            category_id = categories[category_name].id

        account_name = (row.get("account") or row.get("conta") or "").strip()
        account_id = None
        if account_name:
            if account_name.lower() not in accounts:
                acc = Account(name=account_name, user_id=user_id, type="conta_corrente")
                self.db.add(acc)
                self.db.flush()
                accounts[account_name.lower()] = acc
            account_id = accounts[account_name.lower()].id

        paid_at = d if status_value in (TransactionStatus.paid, TransactionStatus.received) else None
        self.db.add(
            Transaction(
                user_id=user_id,
                description=description,
                amount=amount,
                type=TransactionType(txn_type),
                date=d,
                category_id=category_id,
                account_id=account_id,
                status=status_value,
                paid_at=paid_at,
                observation=row.get("observation") or None,
            )
        )
        result.imported += 1