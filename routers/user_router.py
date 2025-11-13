import re
import string

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from database.database import get_session
from models.models import User, UserCreate
from repositories.user_repo import create_user, get_user_by_email, get_user_by_username
from routers.auth_routes import TokenWithUser, login
from services.security import get_current_active_user, get_password_hash
from utils.logging import logger

router = APIRouter(prefix="/users", tags=["users"])

session: Session = Depends(get_session)
active_user = Depends(get_current_active_user)


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_password(password: str) -> bool:
    has_upper = any(ch.isupper() for ch in password)
    has_special = any(ch in string.punctuation for ch in password)
    long_enough = len(password) >= 8

    return has_upper and has_special and long_enough


@router.post("/register", response_model=TokenWithUser)
async def register_user(user: UserCreate, session: Session = session) -> TokenWithUser:
    """Register a new user and return an access token."""
    valid_email = is_valid_email(user.email)
    if not valid_email:
        logger.debug(f"Invalid email attempted during registration: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect Email")
    valid_password = is_valid_password(user.password)
    if not valid_password:
        logger.debug(f"Weak password attempted during registration for email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must have: min. 8 characters, a special "
            "character and an uppercase letter",
        )
    user_from_database = get_user_by_username(session=session, username=user.username)
    if user_from_database:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    user_from_database = get_user_by_email(session=session, email=user.email)
    if user_from_database:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    user_create = User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=get_password_hash(user.password),
        is_active=True,
    )

    created_user: User | None = create_user(session=session, user=user_create)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User could not be created"
        )

    return await login(
        form_data=OAuth2PasswordRequestForm(
            username=user.username,
            password=user.password,
            scope="",
            grant_type="",
            client_id=None,
            client_secret=None,
        ),
        session=session,
    )


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = active_user) -> User:
    """Get current authenticated user information. Returns user data including role."""
    return current_user
