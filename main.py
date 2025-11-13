from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlmodel import Session, SQLModel, select

from database.database import engine
from models.models import Post, User, UserRole
from routers import (
    admin_router,
    auth_routes,
    comment_router,
    event_router,
    friendship_router,
    post_router,
    user_router,
)
from services.security import get_password_hash
from utils.logging import logger


def create_user_if_not_exists(
    session: Session,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> User | None:
    """
    Create a user if they don't already exist.

    Args:
        session: Database session
        username: User's unique username
        email: User's unique email address
        first_name: User's first name
        last_name: User's last name
        password: Plain text password (will be hashed)
        role: User role (default: USER)
        is_active: Whether the user account is active (default: True)

    Returns:
        User object if created or already exists, None if creation fails
    """
    existing_user = session.exec(select(User).where(User.username == username)).one_or_none()

    if existing_user:
        logger.info(f"User '{username}' already exists. Skipping creation.")
        return existing_user

    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        role=role,
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info(f"Created user '{username}' with role '{role.value}'.")
    return user


def create_sample_posts(session: Session) -> None:
    """
    Create sample posts for testing if they don't already exist.

    Args:
        session: Database session
    """
    existing_posts = session.exec(select(Post)).all()
    if existing_posts:
        logger.info(f"{len(existing_posts)} posts already exist. Skipping sample post creation.")
        return

    testuser = session.exec(select(User).where(User.username == "testuser")).one_or_none()
    testuser2 = session.exec(select(User).where(User.username == "testuser2")).one_or_none()
    admin = session.exec(select(User).where(User.username == "admin")).one_or_none()

    if not testuser or not testuser2 or not admin:
        logger.warning("Cannot create sample posts: required users not found.")
        return

    if not testuser.id or not testuser2.id or not admin.id:
        logger.warning("Cannot create sample posts: user IDs are missing.")
        return

    sample_posts = [
        Post(
            content="Wspólne gotowanie w kuchni na korytarzu to najlepsza forma integracji! "
            "Ktoś ma przepis na dobry makaron? 🍝",
            author_id=testuser.id,
        ),
        Post(
            content="Organizujemy wieczór filmowy w piątek o 20:00. Kto chce dołączyć?",
            author_id=testuser2.id,
        ),
        Post(
            content="Dzisiaj sprzątanie wspólnej kuchni - "
            "dzięki wszystkim za pomoc! Razem jest lepiej",
            author_id=testuser.id,
        ),
        Post(
            content="Informacja: W sobotę o 10:00 planowana jest kontrola pokoi. "
            "Prosimy o porządek",
            author_id=admin.id,
        ),
    ]

    for post in sample_posts:
        session.add(post)

    session.commit()
    logger.info(f"Created {len(sample_posts)} sample posts.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup/shutdown events."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create test users
        create_user_if_not_exists(
            session=session,
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="TestPassword123",
            is_active=True,
        )

        create_user_if_not_exists(
            session=session,
            username="testuser2",
            email="testuser2@example.com",
            first_name="Test2",
            last_name="User2",
            password="TestPassword123",
            is_active=True,
        )

        create_user_if_not_exists(
            session=session,
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="AdminPassword123",
            role=UserRole.ADMIN,
            is_active=True,
        )

        # Create sample posts
        create_sample_posts(session)

    logger.info("Application lifespan startup complete.")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(user_router.router)
app.include_router(admin_router.router)
app.include_router(auth_routes.router)
app.include_router(post_router.router)
app.include_router(comment_router.router)
app.include_router(event_router.router)
app.include_router(friendship_router.router)

origins: list[str] = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    logger.info("Root endpoint accessed, redirecting to /docs")
    return RedirectResponse("/docs")
