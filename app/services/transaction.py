from datetime import datetime
from typing import Tuple
from typing import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app import repository
from app.schemas import Transaction
from app.schemas import TransactionCreate
from app.schemas import TransactionInsert
from app.schemas import User
from app.models import Transaction as TransactionDB
from .account import update_balance


def create_transaction(db: Session,
                       transaction: TransactionCreate,
                       user: User) -> Transaction:
    update_balance(db, transaction, user)
    transaction = repository.create(
        TransactionDB,
        item=TransactionInsert(
            user_id=user.id,
            timestamp=datetime.now(),
            type=transaction.type,
            amount=transaction.amount,
        ),
        result_schema=Transaction,
        db=db
    )
    return transaction


def list_by_options(db: Session,
                    options: Sequence[Tuple[str, str, Any]] = None,
                    order: Tuple[str, str] = ("timestamp", "asc"),
                    limit: int = None,
                    offset: int = None) -> Sequence[Transaction]:
    options = [op for op in options if op[2] is not None]
    transactions = repository.list_by_options(
        TransactionDB,
        result_schema=Transaction,
        options=options,
        order=order,
        limit=limit,
        offset=offset,
        db=db
    )
    return transactions
