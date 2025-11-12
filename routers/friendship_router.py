import http

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database.database import get_session
from models.models import Friendship, FriendshipResponse, FriendshipStatusEnum, User
from repositories import friendship_repo
from services.security import get_current_active_user

router = APIRouter(prefix="/friends", tags=["friends"])

session: Session = Depends(get_session)
current_user: User = Depends(get_current_active_user)


@router.post("/request/{addressee_id}", response_model=FriendshipResponse)
def send_friend_request(
    addressee_id: int,
    session: Session = session,
    current_user: User = current_user,
):
    """Wysyła zaproszenie do znajomych."""
    if current_user.id is None:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED, detail="Could not identify current user"
        )

    # 1. Sprawdź, czy użytkownik nie zaprasza samego siebie
    if current_user.id == addressee_id:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail="Cannot send friend request to yourself"
        )

    # 2. Sprawdź, czy użytkownik, którego zapraszasz, istnieje
    addressee = session.get(User, addressee_id)
    if not addressee:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User to add not found")

    # 3. Sprawdź, czy relacja już nie istnieje (używając funkcji z repo)
    existing_friendship = friendship_repo.get_friendship_any_status(
        session=session, user1_id=current_user.id, user2_id=addressee_id
    )

    if existing_friendship:
        if existing_friendship.status == FriendshipStatusEnum.ACCEPTED:
            detail = "Users are already friends"
        elif existing_friendship.status == FriendshipStatusEnum.PENDING:
            detail = "Friendship request already pending"
        else:
            if existing_friendship.status == FriendshipStatusEnum.DECLINED:
                existing_friendship.status = FriendshipStatusEnum.PENDING
                existing_friendship.requester_id = current_user.id
                existing_friendship.addressee_id = addressee_id
                updated_friendship = friendship_repo.update_friendship(
                    session=session, friendship=existing_friendship
                )
                return updated_friendship

            detail = "Friendship relationship already exists"

        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST,
            detail=detail,
        )

    # 4. Stwórz nową relację
    new_friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=addressee_id,
        status=FriendshipStatusEnum.PENDING,
    )

    created_friendship = friendship_repo.create_friendship(
        session=session, friendship=new_friendship
    )
    return created_friendship


@router.put("/accept/{requester_id}", response_model=FriendshipResponse)
def accept_friend_request(
    requester_id: int,
    session: Session = session,
    current_user: User = current_user,
):
    """Akceptuje zaproszenie do znajomych."""
    if current_user.id is None:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED, detail="Could not identify current user"
        )

    # 1. Znajdź oczekujące zaproszenie
    pending_friendship = friendship_repo.get_pending_friendship(
        session=session, requester_id=requester_id, addressee_id=current_user.id
    )

    # 2. Sprawdź, czy zaproszenie istnieje
    if not pending_friendship:
        raise HTTPException(
            status_code=http.HTTPStatus.NOT_FOUND, detail="No pending friend request found"
        )

    # 3. Zmień status na ACCEPTED
    pending_friendship.status = FriendshipStatusEnum.ACCEPTED

    # 4. Zaktualizuj wpis w bazie danych
    updated_friendship = friendship_repo.update_friendship(
        session=session, friendship=pending_friendship
    )

    return updated_friendship


@router.put("/decline/{requester_id}", response_model=FriendshipResponse)
def decline_friend_request(
    requester_id: int,
    session: Session = session,
    current_user: User = current_user,
):
    """Odrzuca zaproszenie do znajomych."""
    if current_user.id is None:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED, detail="Could not identify current user"
        )

    # 1. Znajdź oczekujące zaproszenie
    pending_friendship = friendship_repo.get_pending_friendship(
        session=session, requester_id=requester_id, addressee_id=current_user.id
    )

    # 2. Sprawdź, czy zaproszenie istnieje
    if not pending_friendship:
        raise HTTPException(
            status_code=http.HTTPStatus.NOT_FOUND, detail="No pending friend request found"
        )

    # 3. Zmień status na DECLINED
    pending_friendship.status = FriendshipStatusEnum.DECLINED

    # 4. Zaktualizuj wpis w bazie danych
    updated_friendship = friendship_repo.update_friendship(
        session=session, friendship=pending_friendship
    )

    return updated_friendship


@router.delete("/remove/{friend_id}", response_model=FriendshipResponse)
def remove_friend(
    friend_id: int,
    session: Session = session,
    current_user: User = current_user,
):
    """Usuwa znajomego (zmienia status relacji)."""
    if current_user.id is None:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED, detail="Could not identify current user"
        )

    # 1. Sprawdź, czy użytkownik nie usuwa samego siebie
    if current_user.id == friend_id:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail="Cannot remove yourself"
        )

    # 2. Znajdź zaakceptowaną relację między zalogowanym użytkownikiem a friend_id
    accepted_friendship = friendship_repo.get_accepted_friendship(
        session=session, user1_id=current_user.id, user2_id=friend_id
    )

    # 3. Sprawdź, czy taka relacja istnieje
    if not accepted_friendship:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="Friendship not found")

    # 4. Zmień status, aby "usunąć" przyjaźń
    accepted_friendship.status = FriendshipStatusEnum.DECLINED

    # 5. Zaktualizuj wpis w bazie
    updated_friendship = friendship_repo.update_friendship(
        session=session, friendship=accepted_friendship
    )

    return updated_friendship
