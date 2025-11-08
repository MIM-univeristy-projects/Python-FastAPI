from fastapi.testclient import TestClient
from sqlmodel import Session

from models.models import User


def test_read_all_users_success(client: TestClient, session: Session, logged_in_admin):
    user1 = User(
        email="user1@example.com",
        username="user1",
        first_name="User",
        last_name="One",
        hashed_password="test",
    )
    user2 = User(
        email="user2@example.com",
        username="user2",
        first_name="User",
        last_name="Two",
        hashed_password="test",
    )
    session.add(user1)
    session.add(user2)
    session.commit()
    session.refresh(user1)
    session.refresh(user2)

    response = client.get("/admin/users", headers=logged_in_admin["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_read_user_by_username_success(client: TestClient, session: Session, logged_in_admin):
    user = User(
        email="example@example.com",
        username="example",
        first_name="Example",
        last_name="User",
        hashed_password="test",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    response = client.get(f"/admin/user/{user.username}", headers=logged_in_admin["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == "example"


def test_read_user_by_email_success(client: TestClient, session: Session, logged_in_admin):
    user = User(
        email="example@example.com",
        username="example",
        first_name="Example",
        last_name="User",
        hashed_password="test",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    response = client.get(f"/admin/user/{user.email}", headers=logged_in_admin["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "example@example.com"


def test_read_user_by_username_not_found(client: TestClient, logged_in_admin):
    response = client.get("/admin/user/nonexistentuser", headers=logged_in_admin["headers"])
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"


def test_read_all_users_unauthorized(client: TestClient):
    response = client.get("/admin/users")
    assert response.status_code == 401
