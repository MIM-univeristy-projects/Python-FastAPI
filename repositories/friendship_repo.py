from sqlmodel import Session, or_, select

from models.models import Friendship, FriendshipStatusEnum


def get_friendship_any_status(session: Session, user1_id: int, user2_id: int) -> Friendship | None:
    """Sprawdza, czy istnieje jakakolwiek relacja między dwoma użytkownikami."""
    statement = select(Friendship).where(
        or_(
            (Friendship.requester_id == user1_id) & (Friendship.addressee_id == user2_id),
            (Friendship.requester_id == user2_id) & (Friendship.addressee_id == user1_id),
        )
    )
    return session.exec(statement).one_or_none()


def get_pending_friendship(
    session: Session, requester_id: int, addressee_id: int
) -> Friendship | None:
    """Wyszukuje oczekujące zaproszenie od requester_id do addressee_id."""
    statement = select(Friendship).where(
        Friendship.requester_id == requester_id,
        Friendship.addressee_id == addressee_id,
        Friendship.status == FriendshipStatusEnum.PENDING,
    )
    return session.exec(statement).one_or_none()


def get_accepted_friendship(session: Session, user1_id: int, user2_id: int) -> Friendship | None:
    """Wyszukuje zaakceptowaną przyjaźń między dwoma użytkownikami."""
    statement = select(Friendship).where(
        or_(
            (Friendship.requester_id == user1_id) & (Friendship.addressee_id == user2_id),
            (Friendship.requester_id == user2_id) & (Friendship.addressee_id == user1_id),
        ),
        Friendship.status == FriendshipStatusEnum.ACCEPTED,
    )
    return session.exec(statement).one_or_none()


def create_friendship(session: Session, friendship: Friendship) -> Friendship:
    """Tworzy nowy wpis relacji w bazie danych."""
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return friendship


def update_friendship(session: Session, friendship: Friendship) -> Friendship:
    """Aktualizuje istniejącą relację (np. zmienia status)."""
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return friendship
