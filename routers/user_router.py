import http
import re
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database.database import get_session
from models.models import User, UserCreate
from repositories.user_repo import create_user, get_user_by_email, get_user_by_username
from services.security import get_password_hash

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
    user = get_user_by_username(session, user_username)
    if not user:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_email}")
def read_user_by_email(user_email: str, session: Session = session) -> User | None:
    user = get_user_by_email(session, user_email)
    if not user:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
    return user


@router.post("/register")
def register_user(user: UserCreate, session: Session = session):
    valid_email = is_valid_email(user.email)
    if not valid_email:
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail="Incorrect Email")
    valid_password = is_valid_password(user.password)
    if not valid_password:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST,
            detail="Password must have: 8 characters, a special character and an uppercase letter",
        )
    user_from_database = get_user_by_username(session=session, username=user.username)
    if user_from_database:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail="Username already exists"
        )
    user_from_database = get_user_by_email(session=session, email=user.email)
    if user_from_database:
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail="Email already exists")

    user_create = User(
        id=None,
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
    )

    return create_user(session=session, user=user_create)
