from fastapi.testclient import TestClient

from models.models import FriendshipScenario, User


def get_auth_headers(client: TestClient, username: str, password: str = "testpassword"):
    """Pomocnik do logowania i pobierania tokena."""
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_read_accepted_friends(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /friends/ - should return a list of accepted friends."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/", headers=headers)

    assert response.status_code == 200
    friends_list: list[User] = response.json()

    assert isinstance(friends_list, list)
    assert len(friends_list) == 1
    assert friends_list[0].username == "UserB"


def test_read_pending_requests(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /friends/pending - should return a list of received friend requests."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/pending", headers=headers)

    assert response.status_code == 200
    pending_list: list[User] = response.json()

    assert isinstance(pending_list, list)
    assert len(pending_list) == 1
    assert pending_list[0].username == "UserC"


def test_read_sent_requests(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /friends/sent - should return a list of sent friend requests."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/sent", headers=headers)

    assert response.status_code == 200
    sent_list: list[User] = response.json()

    assert isinstance(sent_list, list)
    assert len(sent_list) == 1
    assert sent_list[0].username == "UserD"
