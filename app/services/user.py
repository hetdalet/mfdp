import secrets
from typing import Any
from typing import Tuple
from typing import Sequence

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import repository
from app.core import auth
from app.models import User as UserDB
from app.schemas import User
from app.schemas import AccountCreate
from app.schemas import UserCreate
from app.schemas import UserExt
from . import account


def get_by_id(db: Session,
              user_id: int,
              result_schema: BaseModel = UserExt):
    return repository.read_by_id(UserDB, user_id, result_schema, db)


def get_by_email(db: Session,
                 email: str,
                 result_schema: BaseModel = UserExt):
    user = repository.read_by_id(
        UserDB,
        email,
        result_schema,
        db,
        id_field="email"
    )
    return user


def get_by_tg_id(db: Session,
                 tg_id: int,
                 result_schema: BaseModel = UserExt):
    user = repository.read_by_id(
        UserDB,
        tg_id,
        result_schema,
        db,
        id_field="tg_id"
    )
    return user


def get_by_tg_link_token(db: Session,
                         tg_link_token: str,
                         result_schema: BaseModel = UserExt):
    user = repository.read_by_id(
        UserDB,
        tg_link_token,
        result_schema,
        db,
        id_field="tg_link_token"
    )
    return user


def list_by_options(db: Session,
                    options: Sequence[Tuple[str, str, Any]] = None,
                    order: Tuple[str, str] = ("timestamp", "asc"),
                    limit: int = None,
                    offset: int = None) -> Sequence[UserExt]:
    users = repository.list_by_options(
        UserDB,
        result_schema=UserExt,
        options=options,
        order=order,
        limit=limit,
        offset=offset,
        db=db
    )
    return users


def create(db: Session, user: UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    user = repository.create(
        UserDB,
        item=UserCreate(email=user.email, password=hashed_password),
        result_schema=User,
        db=db
    )
    account.create(AccountCreate(user_id=user.id), db)
    return user


def deactivate(db: Session, user_id: int):
    user = get_by_id(db, user_id)
    if not user:
        return
    user.deactivated = True
    user = repository.update(
        UserDB,
        item=User(**user.dict()),
        result_schema=User,
        db=db
    )
    return user


def make_tg_link(db: Session, user: User):
    link_token = secrets.token_urlsafe(32)
    link = f"https://t.me/ml_billing_bot?start={link_token}"
    user.tg_link_token = link_token
    repository.update(
        UserDB,
        item=user,
        result_schema=User,
        db=db
    )
    return link


def link_tg_account(db: Session, user: User, tg_user_id: int):
    user.tg_id = tg_user_id
    user.tg_link_token = None
    user = repository.update(
        UserDB,
        item=user,
        result_schema=User,
        db=db
    )
    return user
