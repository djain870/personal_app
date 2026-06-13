from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.db.session import SessionLocal
from app.models import User


router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if user is None:
        return {"message": "User does not exist"}

    if user.password != password:
        return {"message": "Incorrect password"}

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user", value=user.username)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user")
    return response


@router.get("/create-user")
def create_user():
    db = SessionLocal()

    user = User(username="admin", password="1234")
    db.add(user)
    db.commit()
    db.close()

    return {"message": "User created"}


@router.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        db.close()
        return {"message": "Username already exists"}

    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    db.close()

    return RedirectResponse(url="/login", status_code=303)
