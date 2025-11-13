from fastapi.testclient import TestClient

from models.models import FriendshipScenario, User


def get_auth_headers(client: TestClient, username: str, password: str = "testpassword"):
    """Pomocnik do logowania i pobierania tokena."""
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_read_accepted_friends(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /?filter_type=accepted - should return a list of accepted friends."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friendships/", headers=headers)

    assert response.status_code == 200
    friends_data = response.json()

    assert isinstance(friends_data, list)
    assert len(friends_data) == 1

    friends_list = [User(**user) for user in friends_data]
    assert friends_list[0].username == "UserB"


def test_read_accepted_friends_explicit(
    client: TestClient, setup_friendship_scenario: FriendshipScenario
):
    """Tests GET /?filter_type=accepted (explicit) - should return a list of accepted friends."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friendships/?filter_type=accepted", headers=headers)

    assert response.status_code == 200
    friends_data = response.json()

    assert isinstance(friends_data, list)
    assert len(friends_data) == 1

    friends_list = [User(**user) for user in friends_data]
    assert friends_list[0].username == "UserB"


def test_read_pending_requests(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /?filter_type=pending - should return a list of received friend requests."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friendships/?filter_type=pending", headers=headers)

    assert response.status_code == 200
    pending_data = response.json()

    assert isinstance(pending_data, list)
    assert len(pending_data) == 1

    pending_list = [User(**user) for user in pending_data]
    assert pending_list[0].username == "UserC"


def test_read_sent_requests(client: TestClient, setup_friendship_scenario: FriendshipScenario):
    """Tests GET /?filter_type=sent - should return a list of sent friend requests."""
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friendships/?filter_type=sent", headers=headers)

    assert response.status_code == 200
    sent_data = response.json()

    assert isinstance(sent_data, list)
    assert len(sent_data) == 1

    sent_list = [User(**user) for user in sent_data]
    assert sent_list[0].username == "UserD"
