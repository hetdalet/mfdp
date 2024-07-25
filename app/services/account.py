from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.domain_types import TransactionType
from app.models import Account as AccountDB
from app.schemas import Account
from app.schemas import AccountCreate
from app.schemas import TransactionCreate
from app.schemas import User
from app import repository


def create(data: AccountCreate, db: Session):
    return repository.create(AccountDB, data, Account, db)


def get_by_user_id(db: Session, user_id: int):
    account = repository.read_by_id(
        AccountDB,
        user_id,
        Account,
        db,
        id_field="user_id"
    )
    return account


def update_balance(db: Session,
                   transaction: TransactionCreate,
                   user: User):
    credits_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Not enough credits"
    )
    account = get_by_user_id(db, user.id)
    balance = account.balance
    delta = transaction.amount
    if transaction.type == TransactionType.wdr:
        delta *= -1
    balance += delta
    if balance < 0:
        raise credits_exception
    account.balance = balance
    account = repository.update(AccountDB, account, Account, db)
    return account
