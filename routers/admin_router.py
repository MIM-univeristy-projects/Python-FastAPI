import http

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database.database import get_session
from models.models import User, UserResponse
from repositories.user_repo import get_user_by_email, get_user_by_username
from services.security import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])

session: Session = Depends(get_session)


@router.get("/username/{username}", response_model=UserResponse)
def read_user_by_username(
    username: str,
    session: Session = session,
    current_admin: User = Depends(get_current_admin_user),
) -> User | None:
    """Admin-only endpoint to get user by username."""
    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
    return user


@router.get("/email/{email}", response_model=UserResponse)
def read_user_by_email(
    email: str,
    session: Session = session,
    current_admin: User = Depends(get_current_admin_user),
) -> User | None:
    """Admin-only endpoint to get user by email."""
    user = get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
    return user
