from json import JSONDecodeError

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Depends
from fastapi import Request
from fastapi import status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas import Transaction
from app.schemas import TransactionCreate
from app.schemas import User
from app.services import transaction as transaction_service
from ...core import deps

router = APIRouter()


async def get_body(request: Request):
    content_type = request.headers.get('Content-Type')
    if content_type is None:
        raise HTTPException(
            status_code=400,
            detail='No Content-Type provided!'
        )
    elif content_type == 'application/json':
        try:
            return await request.json()
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid JSON data')
    elif (content_type == 'application/x-www-form-urlencoded' or
          content_type.startswith('multipart/form-data')):
        try:
            form_data = await request.form()
            form_dict = {key: form_data[key] for key in form_data.keys()}
            return form_dict
        except Exception:
            raise HTTPException(status_code=400, detail='Invalid Form data')
    else:
        raise HTTPException(
            status_code=400,
            detail='Content-Type not supported!'
        )


@router.post("/", response_model=Transaction)
def create_transaction(transaction=Depends(get_body),
                       db: Session = Depends(deps.get_db),
                       current_user: User = Depends(deps.get_cur_user_from_cookie)):
    try:
        transaction = TransactionCreate(**transaction)
    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err)
        )
    transaction = transaction_service.create_transaction(
        db=db,
        transaction=transaction,
        user=current_user
    )
    return transaction
