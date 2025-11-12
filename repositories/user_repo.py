from sqlmodel import Session, select

from models.models import User


def get_user_by_email(session: Session, email: str) -> User | None:
    user = session.exec(select(User).where(User.email == email)).one_or_none()
    return user


def get_user_by_username(session: Session, username: str) -> User | None:
    user = session.exec(select(User).where(User.username == username)).one_or_none()
    return user


def create_user(session: Session, user: User) -> User | None:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_id(session: Session, user_id: int) -> User | None:
    """Pobiera użytkownika na podstawie jego ID."""
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).one_or_none()
