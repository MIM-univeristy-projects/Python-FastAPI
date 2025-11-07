import http
import re
import string
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from database.database import get_session
from models.models import TokenResponse, User, UserCreate, UserResponse
from repositories.user_repo import create_user, get_user_by_email, get_user_by_username
from services.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)

router = APIRouter(prefix="/users", tags=["users"])

session: Session = Depends(get_session)


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_password(password: str):
    has_upper = any(ch.isupper() for ch in password)
    has_special = any(ch in string.punctuation for ch in password)
    long_enough = len(password) >= 8

    return has_upper and has_special and long_enough


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
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_active=True,
    )

    return create_user(session=session, user=user_create)


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = session
) -> TokenResponse:
    """
    OAuth2 compatible token login. Use username and password to get an access token.
    Returns token along with user information including role for frontend routing.
    The other fields (grant_type, scope, client_id, client_secret) are optional
    and can be left empty.
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User ID not found",
        )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user information. Returns user data including role."""
    return current_user
