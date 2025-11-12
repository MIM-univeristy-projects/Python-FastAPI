import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from models.models import Friendship, FriendshipStatusEnum, User
from services.security import get_password_hash


# Używamy pytest.fixture, aby skonfigurować stan bazy danych przed testami
@pytest.fixture(name="setup_friendship_scenario")
def setup_friendship_scenario_fixture(session: Session):
    """
    Tworzy 4 użytkowników i 3 różne relacje dla UserA:
    - UserA i UserB są znajomymi (ACCEPTED)
    - UserC wysłał zaproszenie do UserA (PENDING, UserA jest adresatem)
    - UserA wysłał zaproszenie do UserD (PENDING, UserA jest zapraszającym)
    """
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

    # Przeładowujemy obiekty, aby uzyskać ich ID
    session.refresh(user_a)
    session.refresh(user_b)
    session.refresh(user_c)
    session.refresh(user_d)

    assert user_a.id is not None
    assert user_b.id is not None
    assert user_c.id is not None
    assert user_d.id is not None

    # Relacja 1: UserA i UserB są znajomymi
    friendship_ab = Friendship(
        requester_id=user_a.id,
        addressee_id=user_b.id,
        status=FriendshipStatusEnum.ACCEPTED,
    )

    # Relacja 2: UserC wysłał zaproszenie do UserA
    friendship_ca = Friendship(
        requester_id=user_c.id,
        addressee_id=user_a.id,
        status=FriendshipStatusEnum.PENDING,
    )

    # Relacja 3: UserA wysłał zaproszenie do UserD
    friendship_ad = Friendship(
        requester_id=user_a.id,
        addressee_id=user_d.id,
        status=FriendshipStatusEnum.PENDING,
    )

    session.add_all([friendship_ab, friendship_ca, friendship_ad])
    session.commit()

    return user_a.id, user_b.id, user_c.id, user_d.id


def get_auth_headers(client: TestClient, username: str, password: str = "testpassword"):
    """Pomocnik do logowania i pobierania tokena."""
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# === TESTY DLA NOWYCH ENDPOINTÓW ===


def test_read_accepted_friends(client: TestClient, setup_friendship_scenario):
    """Testuje GET /friends/ - powinien zwrócić listę zaakceptowanych znajomych."""
    # Logujemy się jako UserA
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/", headers=headers)

    assert response.status_code == 200
    friends_list = response.json()

    # UserA powinien mieć jednego znajomego: UserB
    assert isinstance(friends_list, list)
    assert len(friends_list) == 1
    assert friends_list[0]["username"] == "UserB"


def test_read_pending_requests(client: TestClient, setup_friendship_scenario):
    """Testuje GET /friends/pending - powinien zwrócić listę otrzymanych zaproszeń."""
    # Logujemy się jako UserA
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/pending", headers=headers)

    assert response.status_code == 200
    pending_list = response.json()

    # UserA powinien mieć jedno otrzymane zaproszenie: od UserC
    assert isinstance(pending_list, list)
    assert len(pending_list) == 1
    assert pending_list[0]["username"] == "UserC"


def test_read_sent_requests(client: TestClient, setup_friendship_scenario):
    """Testuje GET /friends/sent - powinien zwrócić listę wysłanych zaproszeń."""
    # Logujemy się jako UserA
    headers = get_auth_headers(client, "UserA")
    response = client.get("/friends/sent", headers=headers)

    assert response.status_code == 200
    sent_list = response.json()

    # UserA powinien mieć jedno wysłane zaproszenie: do UserD
    assert isinstance(sent_list, list)
    assert len(sent_list) == 1
    assert sent_list[0]["username"] == "UserD"
