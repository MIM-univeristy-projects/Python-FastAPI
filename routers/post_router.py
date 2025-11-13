from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database.database import get_session
from models.models import Post, PostReadWithAuthor
from repositories.post_repo import (
    create_post as repo_create_post,
)
from repositories.post_repo import (
    get_all_posts,
    get_post_by_id,
    get_post_with_author,
)

router = APIRouter(prefix="/posts", tags=["posts"])

session: Session = Depends(get_session)


@router.get("/")
def read_posts(session: Session = session) -> list[Post]:
    """Get all posts."""
    return get_all_posts(session)


@router.get("/{post_id}")
def read_post(post_id: int, session: Session = session) -> Post:
    """Get a post by ID."""
    post = get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("/{post_id}/with-author")
def read_post_with_author(post_id: int, session: Session = session) -> PostReadWithAuthor:
    """Get a post by ID with author information."""
    result = get_post_with_author(session, post_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post or author not found"
        )

    post, author = result

    if not post.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Post ID is missing"
        )

    return PostReadWithAuthor(
        id=post.id,
        text=post.text,
        author_id=post.author_id,
        created_at=post.created_at,
        author=author,
    )


@router.post("/")
def create_post(post: Post, session: Session = session) -> Post:
    """Create a new post."""
    return repo_create_post(session, post)
