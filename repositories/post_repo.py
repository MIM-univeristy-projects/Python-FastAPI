from sqlmodel import Session, select

from models.models import Post, User


def get_all_posts(session: Session) -> list[Post]:
    """Get all posts."""
    statement = select(Post)
    return list(session.exec(statement).all())


def get_post_by_id(session: Session, post_id: int) -> Post | None:
    """Get a post by ID."""
    return session.get(Post, post_id)


def get_post_with_author(session: Session, post_id: int) -> tuple[Post, User] | None:
    """Get a post by ID with author information."""
    post = session.get(Post, post_id)
    if not post:
        return None
    author = session.get(User, post.author_id)
    if not author:
        return None
    return (post, author)


def create_post(session: Session, post: Post) -> Post:
    """Create a new post."""
    session.add(post)
    session.commit()
    session.refresh(post)
    return post
