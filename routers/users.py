from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, HTTPException, Form
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

import models
from models import Todos, Users
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix='/users',
    tags=['users']
)


templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return bcrypt_context.hash(password)


@router.get("/profile", response_class=HTMLResponse)
async def change_password(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@router.post("/profile", response_class=HTMLResponse)
async def change_user_password(request: Request, db: Session = Depends(get_db), username: str = Form(...),
                               password: str = Form(...), password2: str = Form(...)):

    user = db.query(models.Users).filter(Users.username == username).first()

    if user is None or not verify_password(password, user.hashed_password):
        msg = "incorrect username or password"
        return templates.TemplateResponse("profile.html", {"request": request, "msg": msg})

    user.hashed_password = get_password_hash(password2)

    db.add(user)
    db.commit()

    msg = "password changed"
    return templates.TemplateResponse("profile.html", {"request": request, "msg": msg})


