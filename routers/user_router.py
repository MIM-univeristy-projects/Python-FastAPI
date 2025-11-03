import http
import re
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database.database import get_session
from models.models import User, UserCreate
from repositories.user_repo import get_user_by_username

router = APIRouter(prefix="/users", tags=["users"])

session: Session = Depends(get_session)


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_password(password):
    has_upper = any(ch.isupper() for ch in password)
    has_special = any(ch in string.punctuation for ch in password)
    long_enough = len(password) >= 8

    return has_upper and has_special and long_enough


@router.get("/{user_username}")
def read_user_by_username(user_username: str, session: Session = session) -> User | None:
    return get_user_by_username(session, user_username)


@router.post("/register")
def register_user(user: UserCreate):
    valid_email = is_valid_email(user.email)
    if not valid_email:
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail="Incorret Email")
    valid_password = is_valid_password(user.password)
    if not valid_password:
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail="Incorret Password")
