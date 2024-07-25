from typing import List
from typing import Optional

from fastapi import APIRouter
from fastapi import Request
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import RedirectResponse
from redis import Redis
from sqlalchemy.orm import Session

from app.core import auth, deps
from app.core.settings import settings
from app.schemas import UserCreate
from app.services import user as user_service
from app.view import templates

router = APIRouter()


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username or not (self.username.__contains__("@")):
            self.errors.append("Email is required")
        if not self.password or not len(self.password) >= 4:
            self.errors.append("A valid password is required")
        if not self.errors:
            return True
        return False


@router.get("/reg")
def reg_get(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("reg.html", context)


@router.post("/reg")
async def reg_post(request: Request, db: Session = Depends(deps.get_db)):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        db_user = user_service.get_by_email(db, email=form.username)
        if db_user:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Email already in use.")
            return templates.TemplateResponse("reg.html", form.__dict__)

        user_service.create(
            db=db,
            user=UserCreate(email=form.username, password=form.password)
        )
        response = RedirectResponse("/auth/login", status.HTTP_302_FOUND)
        return response

    return templates.TemplateResponse("login.html", form.__dict__)


@router.get("/login")
def login_get(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("login.html", context)


@router.post("/login")
async def login_post(request: Request,
                     db: Session = Depends(deps.get_db),
                     rds: Redis = Depends(deps.get_rds)):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response = RedirectResponse("/", status.HTTP_302_FOUND)
            auth.login_for_access_token(
                db,
                rds,
                response=response,
                form_data=form
            )
            form.__dict__.update(msg="Login Successful!")
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Incorrect Email or Password")
            return templates.TemplateResponse("login.html", form.__dict__)
    return templates.TemplateResponse("login.html", form.__dict__)


@router.get("/logout")
def logout_get():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(settings.cookie_name)
    return response
