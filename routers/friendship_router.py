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
    """Sends a friend request to the user with the given ID.

    Args:
        addressee_id (int): ID of the user to send the friend request to
        current_user (User, optional): The user sending the friend request. Defaults to current_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 400 Bad Request if the user tries to send a request to themselves
        HTTPException: 404 Not Found if the addressee user does not exist
        HTTPException: 500 Internal Server Error if the current user is missing an ID
        HTTPException: 409 Conflict if a friendship or request already exists

    Returns:
        Friendship: The created friendship object
    """
    if addressee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sending friend requests to yourself is not allowed.",
        )

    addressee = get_user_by_id(session, addressee_id)
    if not addressee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")

    if not current_user.id:
        logger.error("User missing id identifier")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    existing_friendship = get_friendship_any_status(session, current_user.id, addressee_id)
    if existing_friendship:
        if existing_friendship.status == FriendshipStatusEnum.ACCEPTED:
            detail = "You are already friends."
        elif existing_friendship.status == FriendshipStatusEnum.PENDING:
            detail = "Friend request has already been sent."
        else:
            detail = "User has already declined your friend request."
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
    """Accept a friend request from a user with the given ID.

    Args:
        requester_id (int): ID of the user who sent the friend request
        current_user (User, optional): The user accepting the request.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID
        HTTPException: 404 Not Found if no pending request from this user exists

    Returns:
        Friendship: The updated friendship object with ACCEPTED status
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    pending_request = get_pending_friendship(
        session, requester_id=requester_id, addressee_id=current_user.id
    )
    if not pending_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending friend request found from this user.",
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
    """Decline a friend request from a user with the given ID.

    Args:
        requester_id (int): ID of the user who sent the friend request
        current_user (User, optional): The user declining the request.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID
        HTTPException: 404 Not Found if no pending request from this user exists

    Returns:
        Friendship: The updated friendship object with DECLINED status
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    pending_request = get_pending_friendship(
        session, requester_id=requester_id, addressee_id=current_user.id
    )
    if not pending_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending friend request found from this user.",
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
    """Remove a friend (delete friendship).

    Args:
        friend_id (int): ID of the friend to remove
        current_user (User, optional): The user removing the friend.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID
        HTTPException: 404 Not Found if no friendship exists with this user

    Returns:
        None: Returns 204 No Content on success
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    accepted_friendship = get_accepted_friendship(
        session, user1_id=current_user.id, user2_id=friend_id
    )
    if not accepted_friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not friends with this user.",
        )

    session.delete(accepted_friendship)
    session.commit()
    return


@router.get("/friends/", response_model=list[UserResponse])
def read_friends(
    current_user: User = current_active_user,
    session: Session = session,
) -> list[User]:
    """Get a list of accepted friends.

    Args:
        current_user (User, optional): The user whose friends to retrieve.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID

    Returns:
        list[UserResponse]: List of users who are friends with the current user
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    friends_list = get_accepted_friends(session=session, user_id=current_user.id)
    return friends_list


@router.get("/friends/pending", response_model=list[UserResponse])
def read_pending_requests(
    current_user: User = current_active_user,
    session: Session = session,
):
    """Get a list of received pending friend requests.

    Args:
        current_user (User, optional): The user whose pending requests to retrieve.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID

    Returns:
        list[UserResponse]: List of users who have sent friend requests to current user
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    pending_list = get_received_pending_requests(session=session, user_id=current_user.id)
    return pending_list


@router.get("/friends/sent", response_model=list[UserResponse])
def read_sent_requests(
    current_user: User = current_active_user,
    session: Session = session,
):
    """Get a list of sent pending friend requests.

    Args:
        current_user (User, optional): The user whose sent requests to retrieve.
            Defaults to current_active_user
        session (Session, optional): Database session. Defaults to session.

    Raises:
        HTTPException: 500 Internal Server Error if the current user is missing an ID

    Returns:
        list[UserResponse]: List of users to whom current user has sent friend requests
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User missing id identifier"
        )

    sent_list = get_sent_pending_requests(session=session, user_id=current_user.id)
    return sent_list
