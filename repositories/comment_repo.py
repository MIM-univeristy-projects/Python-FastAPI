from sqlmodel import Session, desc, select

from models.models import Comments, User


def create_comment(session: Session, comment: Comments) -> Comments:
    """Create a new comment."""
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def get_comments_by_post(session: Session, post_id: int) -> list[Comments]:
    """Get all comments for a specific post, ordered by newest first."""
    statement = select(Comments).where(Comments.post_id == post_id).order_by(desc(Comments.created_at))
    return list(session.exec(statement).all())


def get_comment_by_id(session: Session, comment_id: int) -> Comments | None:
    """Get a comment by its ID."""
    return session.get(Comments, comment_id)


def get_comment_with_author(session: Session, comment_id: int) -> tuple[Comments, User] | None:
    """Get a comment by ID with author information."""
    comment = session.get(Comments, comment_id)
    if not comment:
        return None
    author = session.get(User, comment.author_id)
    if not author:
        return None
    return (comment, author)


def get_comments_with_authors(session: Session, post_id: int) -> list[tuple[Comments, User]]:
    """Get all comments for a post with their authors."""
    comments = get_comments_by_post(session, post_id)
    result: list[tuple[Comments, User]] = []
    for comment in comments:
        author = session.get(User, comment.author_id)
        if author:
            result.append((comment, author))
    return result


def delete_comment(session: Session, comment_id: int) -> bool:
    """Delete a comment. Returns True if deleted, False if not found."""
    comment = session.get(Comments, comment_id)
    if not comment:
        return False
    session.delete(comment)
    session.commit()
    return True


def update_comment(session: Session, comment_id: int, new_content: str) -> Comments | None:
    """Update a comment's content. Returns updated comment or None if not found."""
    comment = session.get(Comments, comment_id)
    if not comment:
        return None
    comment.content = new_content
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment
