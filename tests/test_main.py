"""Tests for main application endpoints."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from models.models import Hero, User


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


# Tests for the read_hero endpoint


def test_read_hero_success(client: TestClient, session: Session):
    """Test successfully reading a hero by ID."""
    # Arrange: Create a hero in the test database
    hero = Hero(name="Spider-Boy", secret_name="Pedro Parqueador", age=15)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Act: Make a GET request to the endpoint
    response = client.get(f"/heroes/{hero.id}")

    # Assert: Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == hero.id
    assert data["name"] == "Spider-Boy"
    assert data["secret_name"] == "Pedro Parqueador"
    assert data["age"] == 15


def test_read_hero_not_found(client: TestClient):
    """Test reading a non-existent hero returns 404."""
    # Act: Request a hero that doesn't exist
    response = client.get("/heroes/999")

    # Assert: Verify 404 response
    assert response.status_code == 404
    assert response.json() == {"detail": "Hero not found"}


def test_read_hero_with_null_age(client: TestClient, session: Session):
    """Test reading a hero with null age field."""
    # Arrange: Create a hero without age
    hero = Hero(name="Deadpond", secret_name="Dive Wilson", age=None)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Act: Make a GET request
    response = client.get(f"/heroes/{hero.id}")

    # Assert: Verify the hero is returned with null age
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Deadpond"
    assert data["age"] is None


def test_read_hero_invalid_id_type(client: TestClient):
    """Test that passing invalid ID type returns 422."""
    # Act: Request with a string instead of int
    response = client.get("/heroes/not-a-number")

    # Assert: FastAPI returns 422 for validation error
    assert response.status_code == 422


# Tests for the users endpoint


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
