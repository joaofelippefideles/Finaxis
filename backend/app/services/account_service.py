from fastapi import HTTPException, status
from app.database.session import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.utils.money import money


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRepository(db)

    def list(self, user_id: str, include_inactive: bool = False) -> list[AccountRead]:
        accounts = self.repo.get_by_user(user_id)
        result = []
        for acc in accounts:
            if not include_inactive and not acc.active:
                continue
            result.append(self.to_read(acc))
        return result

    def to_read(self, acc: Account) -> AccountRead:
        return AccountRead(
            id=acc.id,
            user_id=acc.user_id,
            name=acc.name,
            bank=acc.bank,
            type=acc.type,
            initial_balance=acc.initial_balance,
            agency=acc.agency,
            account_number=acc.account_number,
            active=acc.active,
            balance=self.repo.balance(acc),
        )

    def get(self, user_id: str, account_id: str) -> AccountRead:
        acc = self.repo.get_or_404(Account, account_id)
        if acc.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        return self.to_read(acc)

    def create(self, user_id: str, data: AccountCreate) -> AccountRead:
        acc = Account(
            user_id=user_id,
            name=data.name.strip(),
            bank=data.bank,
            type=data.type,
            initial_balance=money(data.initial_balance),
            agency=data.agency,
            account_number=data.account_number,
            active=data.active,
        )
        self.db.add(acc)
        self.db.commit()
        self.db.refresh(acc)
        return self.to_read(acc)

    def update(self, user_id: str, account_id: str, data: AccountUpdate) -> AccountRead:
        acc = self.repo.get_or_404(Account, account_id)
        if acc.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        payload = data.model_dump(exclude_unset=True)
        if "initial_balance" in payload:
            payload["initial_balance"] = money(payload["initial_balance"])
        for field, value in payload.items():
            setattr(acc, field, value)
        self.db.commit()
        self.db.refresh(acc)
        return self.to_read(acc)

    def delete(self, user_id: str, account_id: str) -> None:
        acc = self.repo.get_or_404(Account, account_id)
        if acc.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        used = sum(
            1
            for t in self.db.all(Transaction)
            if t.user_id == user_id
            and account_id in (t.account_id, t.from_account_id, t.to_account_id)
        )
        if used:
            acc.active = False
            self.db.commit()
            return
        self.db.delete(acc)
        self.db.commit()