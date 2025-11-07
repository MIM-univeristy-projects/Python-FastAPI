"""Tests for main application endpoints."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from models.models import User


def test_read_root(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_read_item(client: TestClient):
    """Test the items endpoint."""
    response = client.get("/items/42?q=test")
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == 42
    assert data["q"] == "test"


def test_read_item_no_query(client: TestClient):
    """Test the items endpoint without query parameter."""
    response = client.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == 1
    assert data["q"] is None


def test_read_user_by_username_success(client: TestClient, session: Session):
    user = User(id=1, email="example@example.com", username="example", hashed_password="test")
    session.add(user)
    session.commit()
    session.refresh(user)

    response = client.get(f"/users/{user.username}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == "example"


def test_read_user_by_username_not_found(client: TestClient, session: Session):
    response = client.get("/users/user_not_found")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
