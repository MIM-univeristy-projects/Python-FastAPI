from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database.database import get_session
from models.models import (
    Friendship,
    FriendshipResponse,
    FriendshipStatusEnum,
    User,
    UserResponse,
)
from repositories.friendship_repo import (
    create_friendship,
    get_accepted_friends,
    get_accepted_friendship,
    get_friendship_any_status,
    get_pending_friendship,
    get_received_pending_requests,
    get_sent_pending_requests,
    update_friendship,
)
from repositories.user_repo import get_user_by_id
from services.security import get_current_active_user, get_current_user
from utils.logging import logger

router = APIRouter(tags=["Friendships"])

current_user = Depends(get_current_user)
session = Depends(get_session)
current_active_user = Depends(get_current_active_user)


@router.post(
    "/friends/request/{addressee_id}",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request(
    addressee_id: int,
    current_user: User = current_user,
    session: Session = session,
) -> Friendship:
    """Wysyła zaproszenie do znajomych do użytkownika o podanym ID."""
    if addressee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie można wysłać zaproszenia do samego siebie.",
        )

    addressee = get_user_by_id(session, addressee_id)
    if not addressee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Użytkownik nie istnieje."
        )

    if not current_user.id:
        logger.error("User missing id identifier")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    existing_friendship = get_friendship_any_status(session, current_user.id, addressee_id)
    if existing_friendship:
        if existing_friendship.status == FriendshipStatusEnum.ACCEPTED:
            detail = "Jesteście już znajomymi."
        elif existing_friendship.status == FriendshipStatusEnum.PENDING:
            detail = "Zaproszenie zostało już wysłane."
        else:
            detail = "Użytkownik odrzucił już Twoje zaproszenie."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    new_friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=addressee_id,
        status=FriendshipStatusEnum.PENDING,
    )
    created_friendship = create_friendship(session, new_friendship)
    return created_friendship


@router.post("/friends/accept/{requester_id}", response_model=FriendshipResponse)
def accept_friend_request(
    requester_id: int,
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Akceptuje zaproszenie do znajomych od użytkownika o podanym ID."""
    pending_request = get_pending_friendship(
        session, requester_id=requester_id, addressee_id=current_user.id
    )
    if not pending_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono oczekującego zaproszenia od tego użytkownika.",
        )

    pending_request.status = FriendshipStatusEnum.ACCEPTED
    updated_friendship = update_friendship(session, pending_request)
    return updated_friendship


@router.post("/friends/decline/{requester_id}", response_model=FriendshipResponse)
def decline_friend_request(
    requester_id: int,
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Odrzuca zaproszenie do znajomych od użytkownika o podanym ID."""
    pending_request = get_pending_friendship(
        session, requester_id=requester_id, addressee_id=current_user.id
    )
    if not pending_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono oczekującego zaproszenia od tego użytkownika.",
        )

    pending_request.status = FriendshipStatusEnum.DECLINED
    updated_friendship = update_friendship(session, pending_request)
    return updated_friendship


@router.delete("/friends/remove/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: int,
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Usuwa znajomego (anuluje przyjaźń)."""
    accepted_friendship = get_accepted_friendship(
        session, user1_id=current_user.id, user2_id=friend_id
    )
    if not accepted_friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie jesteście znajomymi.",
        )

    session.delete(accepted_friendship)
    session.commit()
    return


# === NOWE ENDPOINT'Y GET ===


@router.get("/friends/", response_model=list[UserResponse])
def read_friends(
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Pobiera listę zaakceptowanych znajomych."""
    friends_list = get_accepted_friends(session=session, user_id=current_user.id)
    return friends_list


@router.get("/friends/pending", response_model=list[UserResponse])
def read_pending_requests(
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Pobiera listę otrzymanych, oczekujących zaproszeń do znajomych."""
    pending_list = get_received_pending_requests(session=session, user_id=current_user.id)
    return pending_list


@router.get("/friends/sent", response_model=list[UserResponse])
def read_sent_requests(
    current_user: User = current_active_user,
    session: Session = session,
):
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    """Pobiera listę wysłanych, oczekujących zaproszeń do znajomych."""
    sent_list = get_sent_pending_requests(session=session, user_id=current_user.id)
    return sent_list
