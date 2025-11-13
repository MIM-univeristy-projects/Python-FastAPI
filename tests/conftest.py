"""Pytest configuration and fixtures for testing."""

import enum

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from database.database import get_session
from main import app
from models.models import (
    AuthenticatedUser,
    Friendship,
    FriendshipScenario,
    FriendshipStatusEnum,
    User,
    UserRole,
)
from services.security import get_password_hash


class FixtureEnum(str, enum.Enum):
    SESSION = "session"
    CLIENT = "client"
    LOGGED_IN_USER = "logged_in_user"
    LOGGED_IN_ADMIN = "logged_in_admin"
    SETUP_FRIENDSHIP_SCENARIO = "setup_friendship_scenario"


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
def logged_in_user_fixture(client: TestClient, session: Session) -> AuthenticatedUser:
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

    return AuthenticatedUser(
        user=user,
        token=token_data["access_token"],
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )


@pytest.fixture(name=FixtureEnum.LOGGED_IN_ADMIN)
def logged_in_admin_fixture(client: TestClient, session: Session) -> AuthenticatedUser:
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

    return AuthenticatedUser(
        user=admin,
        token=token_data["access_token"],
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )


@pytest.fixture(name=FixtureEnum.SETUP_FRIENDSHIP_SCENARIO)
def setup_friendship_scenario_fixture(session: Session) -> FriendshipScenario:
    """Fixture to set up users and friendships for testing."""
    hashed_password = get_password_hash("testpassword")

    user_a = User(
        email="user_a@test.com",
        username="UserA",
        first_name="User",
        last_name="A",
        hashed_password=hashed_password,
        is_active=True,
    )
    user_b = User(
        email="user_b@test.com",
        username="UserB",
        first_name="User",
        last_name="B",
        hashed_password=hashed_password,
        is_active=True,
    )
    user_c = User(
        email="user_c@test.com",
        username="UserC",
        first_name="User",
        last_name="C",
        hashed_password=hashed_password,
        is_active=True,
    )
    user_d = User(
        email="user_d@test.com",
        username="UserD",
        first_name="User",
        last_name="D",
        hashed_password=hashed_password,
        is_active=True,
    )

    session.add_all([user_a, user_b, user_c, user_d])
    session.commit()

    # Reload objects to get their IDs
    session.refresh(user_a)
    session.refresh(user_b)
    session.refresh(user_c)
    session.refresh(user_d)

    assert user_a.id is not None
    assert user_b.id is not None
    assert user_c.id is not None
    assert user_d.id is not None

    # Relationship 1: UserA and UserB are friends
    friendship_ab = Friendship(
        requester_id=user_a.id,
        addressee_id=user_b.id,
        status=FriendshipStatusEnum.ACCEPTED,
    )

    # Relationship 2: UserC sent a friend request to UserA
    friendship_ca = Friendship(
        requester_id=user_c.id,
        addressee_id=user_a.id,
        status=FriendshipStatusEnum.PENDING,
    )

    # Relationship 3: UserA sent a friend request to UserD
    friendship_ad = Friendship(
        requester_id=user_a.id,
        addressee_id=user_d.id,
        status=FriendshipStatusEnum.PENDING,
    )

    session.add_all([friendship_ab, friendship_ca, friendship_ad])
    session.commit()

    return FriendshipScenario(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        user_c_id=user_c.id,
        user_d_id=user_d.id,
    )
