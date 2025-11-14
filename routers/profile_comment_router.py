from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database.database import get_session
from models.models import CommentRequest, ProfileComment, ProfileCommentWithAuthor, User
from repositories.profile_comment_repo import (
    create_profile_comment,
    delete_profile_comment,
    get_profile_comment_by_id,
    get_profile_comments_with_authors,
    update_profile_comment,
)
from repositories.user_repo import get_user_by_id
from services.security import get_current_active_user
from utils.logging import logger

router = APIRouter(prefix="/users", tags=["profile-comments"])

session: Session = Depends(get_session)
current_user = Depends(get_current_active_user)


@router.post("/{user_id}/comments", status_code=status.HTTP_201_CREATED)
def create_profile_comment_endpoint(
    user_id: int,
    comment_data: CommentRequest,
    current_user: User = current_user,
    session: Session = session,
) -> ProfileCommentWithAuthor:
    """Create a new comment on a user profile. Requires authentication."""
    # Check if profile user exists
    profile_user = get_user_by_id(session, user_id)
    if not profile_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not current_user.id:
        logger.error("User ID is missing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is missing"
        )

    new_comment = ProfileComment(
        content=comment_data.content,
        author_id=current_user.id,
        profile_user_id=user_id,
    )

    created_comment = create_profile_comment(session, new_comment)

    if not created_comment.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Comment ID is missing"
        )

    return ProfileCommentWithAuthor(
        id=created_comment.id,
        content=created_comment.content,
        author_id=created_comment.author_id,
        profile_user_id=created_comment.profile_user_id,
        created_at=str(created_comment.created_at),
        author_name=current_user.username,
    )


@router.get("/{user_id}/comments")
def get_profile_comments_endpoint(
    user_id: int,
    session: Session = session,
) -> list[ProfileCommentWithAuthor]:
    """Get all comments for a specific user profile."""
    # Check if profile user exists
    profile_user = get_user_by_id(session, user_id)
    if not profile_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Get comments with authors
    comments_with_authors = get_profile_comments_with_authors(session, user_id)

    # Build response
    result: list[ProfileCommentWithAuthor] = []
    for comment, author in comments_with_authors:
        if not comment.id:
            continue

        result.append(
            ProfileCommentWithAuthor(
                id=comment.id,
                content=comment.content,
                author_id=comment.author_id,
                profile_user_id=comment.profile_user_id,
                created_at=str(comment.created_at),
                author_name=author.username,
            )
        )

    return result


@router.put("/comments/{comment_id}")
def update_profile_comment_endpoint(
    comment_id: int,
    comment_data: CommentRequest,
    current_user: User = current_user,
    session: Session = session,
) -> ProfileCommentWithAuthor:
    """Update a profile comment's content.

    Only the comment author can update. Requires authentication.
    """
    comment = get_profile_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Check if user is the author
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    updated_comment = update_profile_comment(session, comment_id, comment_data.content)
    if not updated_comment:
        logger.error("Failed to update profile comment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update comment"
        )

    if not updated_comment.id:
        logger.error("Comment ID is missing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Comment ID is missing"
        )

    return ProfileCommentWithAuthor(
        id=updated_comment.id,
        content=updated_comment.content,
        author_id=updated_comment.author_id,
        profile_user_id=updated_comment.profile_user_id,
        created_at=str(updated_comment.created_at),
        author_name=current_user.username,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_comment_endpoint(
    comment_id: int,
    current_user: User = current_user,
    session: Session = session,
) -> None:
    """Delete a profile comment.

    Only the comment author or admin can delete. Requires authentication.
    """
    comment = get_profile_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Check if user is the author or an admin
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    was_deleted = delete_profile_comment(session, comment_id)
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete comment"
        )
