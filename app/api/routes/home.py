from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.utils.auth import get_current_user


router = APIRouter()


@router.get("/")
def home(request: Request):
    user = get_current_user(request)

    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("index.html", {"request": request})
