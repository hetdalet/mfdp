from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.schemas import User
from app.models import User as UserDB
from app.models import Account as AccountDB
from app.models import Transaction as TransactionDB


@pytest.mark.fixt_data({
    "user_data": [
        {"id": 1, "email": "user1@example.com", "password": "password_1", "deactivated": None},
        {"id": 2, "email": "user2@example.com", "password": "password_2", "deactivated": None},
    ],
    "account_data": [
        {"id": 1, "user_id": 1, "balance": 0},
        {"id": 2, "user_id": 2, "balance": 0},
    ]
})
def test_create_transaction(fill_tables: Tuple[TestClient, Session],
                            override_get_auth_user):

    def get_balance(session, user_id):
        account = (
            session
            .query(AccountDB)
            .filter(AccountDB.user_id == user_id)
            .first()
        )
        return account.balance

    def list_transactions(session):
        return session.query(TransactionDB).all()

    client, session = fill_tables

    _, override_get_auth_user_ = override_get_auth_user
    user = User(
        id=1,
        email="user1@example.com",
        password="password_1",
        deactivated=None,
        balance=0
    )
    override_get_auth_user_(user)
    assert get_balance(session, user.id) == 0
    transactions = list_transactions(session)
    assert len(transactions) == 0

    response = client.post(
        f"/transactions",
        json={"type": 1, "amount": 20}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 20
    transactions = list_transactions(session)
    assert len(transactions) == 1
    assert transactions[0].user.id == user.id

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 5}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 15
    assert len(list_transactions(session)) == 2

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 5}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 10
    assert len(list_transactions(session)) == 3

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 8}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 2
    assert len(list_transactions(session)) == 4

    response = client.post(
        f"/transactions",
        json={"type": 1, "amount": 3}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 5
    assert len(list_transactions(session)) == 5

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 10}
    )
    assert response.status_code == 400
    assert get_balance(session, user.id) == 5
    assert len(list_transactions(session)) == 5

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 5}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 0
    assert len(list_transactions(session)) == 6

    response = client.post(
        f"/transactions",
        json={"type": 2, "amount": 1}
    )
    assert response.status_code == 400
    assert get_balance(session, user.id) == 0
    assert len(list_transactions(session)) == 6

    response = client.post(
        f"/transactions",
        json={"type": 1, "amount": 0}
    )
    assert response.status_code == 200
    assert get_balance(session, user.id) == 0
    assert len(list_transactions(session)) == 7

    response = client.post(
        f"/transactions",
        json={"type": 1000, "amount": 10}
    )
    assert response.status_code == 422
    assert get_balance(session, user.id) == 0
    assert len(list_transactions(session)) == 7

    response = client.post(
        f"/transactions",
        json={"type": 1, "amount": -1}
    )
    assert response.status_code == 422
    assert get_balance(session, user.id) == 0
    assert len(list_transactions(session)) == 7
