"""Tests for main application endpoints."""
from fastapi.testclient import TestClient


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
