from datetime import datetime
from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.schemas import Account
from app.schemas import User
from app.schemas import UserCreate
from app.schemas import UserExt
from app.schemas import Transaction
from app.schemas import Task
from app.schemas import TgLink
from app.schemas import TgAccLinkRequest
from app.services import account as account_service
from app.services import user as user_service
from app.services import task as task_service
from app.services import transaction as transaction_service
from ...core import deps

router = APIRouter()


@router.post("/", response_model=User)
def create_user(user: UserCreate,
                db: Session = Depends(deps.get_db)):
    db_user = user_service.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = user_service.create(db=db, user=user)
    return user


@router.get("/", response_model=UserExt)
def get_current_user(current_user: User = Depends(deps.get_cur_user_from_cookie)) -> User:
    return current_user


@router.get("/{user_id}", response_model=UserExt)
def get_user(user_id: int,
             account: bool | None = None,
             db: Session = Depends(deps.get_db),
             current_user: User = Depends(deps.get_cur_user_from_cookie)) -> User:
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    user = current_user
    if account:
        account = account_service.get_by_user_id(db, user_id)
        user = UserExt(**user.dict())
        user.account = account
    return user


@router.get("/{user_id}/account", response_model=Account)
def get_account(user_id: int,
                db: Session = Depends(deps.get_db),
                current_user: User = Depends(deps.get_cur_user_from_cookie)) -> User:
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    return account_service.get_by_user_id(db, user_id)


@router.delete("/{user_id}")
def deactivate_user(user_id: int,
                    db: Session = Depends(deps.get_db),
                    current_user: User = Depends(deps.get_cur_user_from_cookie)):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    user_service.deactivate(db=db, user_id=user_id)


@router.get("/{user_id}/transactions", response_model=List[Transaction])
def list_transactions(user_id: int,
                      limit: int = None,
                      offset: int = None,
                      tss: datetime = None,
                      tse: datetime = None,
                      db: Session = Depends(deps.get_db),
                      current_user: User = Depends(deps.get_cur_user_from_cookie)):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    transactions = transaction_service.list_by_options(
        db=db,
        options=(
            ("user_id", "==", user_id),
            ("timestamp", ">=", tss),
            ("timestamp", "<", tse),
        ),
        limit=limit,
        offset=offset
    )
    return transactions


@router.get("/{user_id}/tasks", response_model=List[Task])
def list_tasks(user_id: int,
               sn: str = None,
               limit: int = None,
               offset: int = None,
               db: Session = Depends(deps.get_db),
               current_user: User = Depends(deps.get_cur_user_from_cookie)):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    options = [("user_id", "==", user_id)]
    if sn:
        options.append(("service_name", "==", sn))
    tasks = task_service.list_by_options(
        db=db,
        options=options,
        limit=limit,
        offset=offset
    )
    return tasks


@router.get("/tg/{tg_user_id}", response_model=UserExt)
def get_by_tg_id(tg_user_id: int, db: Session = Depends(deps.get_db)):
    user = user_service.get_by_tg_id(db, tg_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/{user_id}/tg/link", response_model=TgLink)
def make_tg_link(user_id: int,
                 db: Session = Depends(deps.get_db),
                 current_user: User = Depends(deps.get_cur_user_from_cookie)):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    user = user_service.get_by_id(db, user_id, result_schema=User)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.tg_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a linked Telegram account"
        )
    link = user_service.make_tg_link(db, user)
    return TgLink(link=link)


@router.post("/tg/link_acc", response_model=UserExt)
def link_tg_account(link_data: TgAccLinkRequest,
                    db: Session = Depends(deps.get_db)):
    link_token = link_data.link_token
    user = user_service.get_by_tg_link_token(db, link_token, result_schema=User)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link expired"
        )
    if user.tg_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a linked Telegram account"
        )
    user_service.link_tg_account(db, user, link_data.tg_user_id)
    return user
