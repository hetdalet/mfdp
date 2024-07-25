import json
from datetime import datetime
from datetime import timezone
from datetime import timedelta
from typing import Dict
from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.openapi.models import OAuthFlows
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from jose import JWTError
from passlib.context import CryptContext
from redis import Redis
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from app.core.settings import settings
from app.schemas import TokenData
from app.schemas import UserCreate
from app.services import user as user_service

SIG_ALGO = "HS256"


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):

    def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get(settings.cookie_name)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def decode_token(token: str):
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token",
    )
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[SIG_ALGO]
        )
    except JWTError as err:
        raise token_exception

    username: str = payload.get("username")
    if username is None:
        raise token_exception

    return TokenData(username=username)


def authenticate_user(db: Session, username: str, password: str):
    user = user_service.get_by_email(db, username, result_schema=UserCreate)
    if not user:
        return
    if not verify_password(password, user.password):
        return
    return user


def authenticate_cookie(db: Session, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign in for access"
        )
    token = token.removeprefix('Bearer')[1:]
    decoded_token = decode_token(token)
    user = user_service.get_by_email(db, decoded_token.username)
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    data = data.copy()
    expires_delta = expires_delta or timedelta(days=1)
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(
        data,
        settings.auth_secret_key,
        algorithm=SIG_ALGO
    )
    return encoded_jwt


def login_for_access_token(db: Session,
                           rds: Redis,
                           response: Response,
                           form_data) -> Dict[str, str]:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"username": user.email})
    cookie_val = f"Bearer {access_token}"
    response.set_cookie(
        key=settings.cookie_name,
        value=cookie_val,
        httponly=True
    )
    if user.tg_id:
        set_tg_session(rds, user.id, user.tg_id, cookie_val)
    return {settings.cookie_name: access_token, "token_type": "bearer"}


def set_tg_session(rds: Redis, user_id, tg_user_id: int, cookie_val: str):
    session_data = {
        "user_id": user_id,
        "cookie": {settings.cookie_name: cookie_val}
    }
    rds.set(str(tg_user_id), json.dumps(session_data))
