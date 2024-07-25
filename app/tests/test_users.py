from typing import Callable
from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.schemas import User
from app.schemas import UserExt
from app.models import User as UserDB
from app.models import Account as AccountDB
from app.domain_types import TransactionType


def test_create_user(override_session: Tuple[TestClient, Session]):
    client, session = override_session
    email = "user1@example.com"
    response = client.post(
        "/users/",
        json={"email": email, "password": "12345"},
    )
    assert response.status_code == 200
    user = User(**response.json())
    assert user.email == email
    account = (
        session.query(AccountDB)
        .filter(AccountDB.user_id == user.id)
        .first()
    )
    assert account.balance == 0

    response = client.post(
        "/users/",
        json={"email": email, "password": "12345"},
    )
    assert response.status_code == 400
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Email already registered"

    email = "user2@example.com"
    response = client.post(
        "/users/",
        json={"email": email, "password": "12345"},
    )
    assert response.status_code == 200
    user = User(**response.json())
    assert user.email == email
    account = session.query(AccountDB).filter(UserDB.id == user.id).first()
    assert account.balance == 0


@pytest.mark.fixt_data({
    "user_data": [{"id": 1, "email": "user1@example.com", "password": "password_1"}],
    "account_data": [{"id": 1, "user_id": 1, "balance": 10}]
})
def test_get_user(fill_tables,
                  override_get_auth_user):
    client, session = fill_tables
    _, override_get_auth_user_ = override_get_auth_user
    cur_user_id = 1
    override_get_auth_user_(User(
        id=cur_user_id,
        email="user1@example.com",
        password="password_1",
        deactivated=None,
        balance=0
    ))
    response = client.get(f"/users/1")
    assert response.status_code == 200
    user = UserExt(**response.json())
    assert user.email == "user1@example.com"

    response = client.get(f"/users/1?account=true")
    assert response.status_code == 200
    user = UserExt(**response.json())
    assert user.email == "user1@example.com"
    assert user.account is not None
    assert user.account.user_id == 1
    assert user.account.balance == 10


@pytest.mark.fixt_data({
    "user_data": [
        {"id": 1, "email": "user1@example.com", "password": "password_1", "deactivated": None},
        {"id": 2, "email": "user2@example.com", "password": "password_2", "deactivated": None},
    ]
})
def test_deactivate_user(fill_tables: Tuple[TestClient, Session],
                         override_get_auth_user):
    client, session = fill_tables
    _, override_get_auth_user_ = override_get_auth_user
    cur_user_id = 1
    other_user_id = 2
    override_get_auth_user_(User(
        id=cur_user_id,
        email="user1@example.com",
        password="password_1",
        deactivated=None,
        balance=0
    ))
    # Deactivate own account
    response = client.delete(f"/users/{cur_user_id}")
    assert response.status_code == 200
    user = session.query(UserDB).filter(UserDB.id == cur_user_id).first()
    assert user.deactivated is True

    # Deactivate deactivated account
    response = client.delete(f"/users/{cur_user_id}")
    assert response.status_code == 200
    user = session.query(UserDB).filter(UserDB.id == cur_user_id).first()
    assert user.deactivated is True

    # Deactivate other account
    response = client.delete(f"/users/{other_user_id}")
    assert response.status_code == 403
    user = session.query(UserDB).filter(UserDB.id == other_user_id).first()
    assert user.deactivated is None


@pytest.mark.fixt_data({
    "user_data": [
        {"id": 1, "email": "user1@example.com", "password": "password_1", "deactivated": None},
        {"id": 2, "email": "user2@example.com", "password": "password_2", "deactivated": None},
    ],
    "transaction_data": [
        {
            "id": 1,
            "user_id": 1,
            "timestamp": "2024-04-26 06:42:23.524345",
            "type": "dep",
            "amount": 20,
            "task_id": None
        },
        {
            "id": 2,
            "user_id": 1,
            "timestamp": "2024-04-26 06:42:40.786371",
            "type": "wdr",
            "amount": 5,
            "task_id": None
        },
        {
            "id": 3,
            "user_id": 1,
            "timestamp": "2024-04-26 06:42:46.680587",
            "type": "wdr",
            "amount": 5,
            "task_id": None
        },
        {
            "id": 4,
            "user_id": 1,
            "timestamp": "2024-04-26 06:42:52.356764",
            "type": "dep",
            "amount": 5,
            "task_id": None
        },
        {
            "id": 5,
            "user_id": 1,
            "timestamp": "2024-04-26 06:43:07.044437",
            "type": "wdr",
            "amount": 10,
            "task_id": None
        }
    ]
})
def test_list_user_transactions(fill_tables: Tuple[TestClient, Session],
                                override_get_auth_user):
    client, session = fill_tables
    _, override_get_auth_user_ = override_get_auth_user
    cur_user_id = 1
    other_user_id = 2
    override_get_auth_user_(User(
        id=cur_user_id,
        email="user1@example.com",
        password="password_1",
        deactivated=None,
        balance=0
    ))
    # List own transactions
    response = client.get(f"/users/{cur_user_id}/transactions")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 5

    # List with custom limit
    response = client.get(f"/users/{cur_user_id}/transactions?limit=3")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 3

    # List with custom limit and offset
    response = client.get(f"/users/{cur_user_id}/transactions?limit=1&offset=2")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["id"] == 3

    # List other's transactions
    response = client.get(f"/users/{other_user_id}/transactions")
    assert response.status_code == 403

    # List own transactions
    response = client.get(f"/users/{cur_user_id}/transactions")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 5

    # User without transactions
    override_get_auth_user_(User(
        id=other_user_id,
        email="user2@example.com",
        password="password_2",
        deactivated=None,
        balance=0
    ))
    response = client.get(f"/users/{other_user_id}/transactions")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 0


