from fastapi import APIRouter
from fastapi import Request
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from fastapi import Depends
from app.core import auth, deps
from app.core.settings import settings
from app.services import account as account_service
from app.view import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def get_main_page(request: Request, db: Session = Depends(deps.get_db)):
    token = request.cookies.get(settings.cookie_name)
    if token:
        user = auth.authenticate_cookie(db, token)
    else:
        response = RedirectResponse("/auth/login", status.HTTP_302_FOUND)
        return response
    context = {
        "user": user,
        "request": request
    }
    if user:
        account = account_service.get_by_user_id(db, user.id)
        context["balance"] = account.balance
        return templates.TemplateResponse("index.html", context)
