"""Pytest configuration and fixtures for testing."""

import enum

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from database.database import get_session
from main import app
from models.models import User, UserRole
from services.security import get_password_hash


class FixtureEnum(str, enum.Enum):
    SESSION = "session"
    CLIENT = "client"
    LOGGED_IN_USER = "logged_in_user"
    LOGGED_IN_ADMIN = "logged_in_admin"


@pytest.fixture(name=FixtureEnum.SESSION)
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name=FixtureEnum.CLIENT)
def client_fixture(session: Session):
    """Create a test client with overridden database session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name=FixtureEnum.LOGGED_IN_USER)
def logged_in_user_fixture(client: TestClient, session: Session):
    """Create a logged-in regular user and return user data with access token."""
    # Create a test user
    user = User(
        email="testuser@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.USER,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Login to get access token
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    token_data = response.json()

    return {
        "user": user,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest.fixture(name=FixtureEnum.LOGGED_IN_ADMIN)
def logged_in_admin_fixture(client: TestClient, session: Session):
    """Create a logged-in admin user and return user data with access token."""
    # Create a test admin user
    admin = User(
        email="admin@example.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpassword"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)

    # Login to get access token
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "adminpassword"},
    )
    assert response.status_code == 200
    token_data = response.json()

    return {
        "user": admin,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }
