from fastapi import APIRouter, Depends
from sqlmodel import Session

from database.database import get_session
from models.models import User
from repositories.user_repo import get_user_by_username

router = APIRouter(prefix="/users", tags=["users"])

session: Session = Depends(get_session)


@router.get("/{user_username}")
def read_user_by_username(user_username: str, session: Session = session) -> User | None:
    return get_user_by_username(session, user_username)
