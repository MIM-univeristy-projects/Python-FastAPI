from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

# from routers import example_router, user_router
from database.database import engine
from models.models import User, UserRole
from routers import admin_router, auth_routes, example_router, user_router
from services.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup/shutdown events."""
    SQLModel.metadata.create_all(engine)
    user: User = User(
        username="testuser",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123"),
        is_active=True,
    )
    with Session(engine) as session:
        existing_user = session.exec(
            select(User).where(User.username == user.username)
        ).one_or_none()
        if not existing_user:
            session.add(user)
            session.commit()
            session.refresh(user)

    admin: User = User(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("AdminPassword123"),
        is_active=True,
        role=UserRole.ADMIN,
    )
    with Session(engine) as session:
        existing_user = session.exec(
            select(User).where(User.username == admin.username)
        ).one_or_none()
        if not existing_user:
            session.add(admin)
            session.commit()
            session.refresh(admin)

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(example_router.router)
app.include_router(user_router.router)
app.include_router(admin_router.router)
app.include_router(auth_routes.router)

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
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
