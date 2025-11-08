"""Tests for main application endpoints."""

from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
