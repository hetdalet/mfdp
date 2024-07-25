import time
from typing import Tuple
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.schemas import User
from app.models import Account as AccountDB
from app.models import Transaction as TransactionDB
from app.models import Task as TaskDB


@pytest.mark.fixt_data({
    "user_data": [
        {"id": 1, "email": "user1@example.com", "password": "password_1", "deactivated": None},
        {"id": 2, "email": "user2@example.com", "password": "password_2", "deactivated": None},
    ],
    "account_data": [
        {"id": 1, "user_id": 1, "balance": 20},
        {"id": 2, "user_id": 2, "balance": 0},
    ],
    "service_data": [
        {
            "name": "dummy",
            "description": "Dummy service",
            "pricing_type": "fixed",
            "price": 5,
        },
    ],
})
def test_task(monkeypatch,
              fill_tables: Tuple[TestClient, Session],
              override_get_auth_user,
              override_get_rmq):

    def get_balance(session, user_id):
        account = (
            session
            .query(AccountDB)
            .filter(AccountDB.user_id == user_id)
            .first()
        )
        return account.balance

    def list_user_transactions(session, user_id):
        transactions = (
            session.query(TransactionDB)
            .filter(TransactionDB.user_id == user_id)
            .all()
        )
        return transactions

    def list_user_tasks(session, user_id):
        tasks = (
            session.query(TaskDB)
            .filter(TaskDB.user_id == user_id)
            .all()
        )
        return tasks

    monkeypatch.setattr("app.services.task.send_task_to_queue", Mock())
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
    assert get_balance(session, user.id) == 20
    transactions = list_user_transactions(session, user.id)
    assert len(transactions) == 0
    tasks = list_user_tasks(session, user.id)
    assert len(tasks) == 0

    service_name = "dummy"
    task_input = "dummy input"
    response = client.post(
        f"/services/{service_name}/task",
        json={"input": task_input}
    )
    assert response.status_code == 200, response.json()
    assert get_balance(session, user.id) == 15
    transactions = list_user_transactions(session, user.id)
    assert len(transactions) == 1
    assert transactions[0].user.id == user.id
    transaction = transactions[0]
    tasks = list_user_tasks(session, user.id)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.user.id == user.id
    assert task.service_name == service_name
    assert task.transaction.id == transaction.id
    assert task.input == task_input

    output = "dummy output"
    time.sleep(1)
    response = client.patch(
        f"/tasks/{task.key}",
        json={"output": output}
    )
    assert response.status_code == 200, response.json()
    finished_task = list_user_tasks(session, user.id)[0]
    assert finished_task.user.id == user.id
    assert finished_task.service_name == service_name
    assert finished_task.transaction.id == transaction.id
    assert finished_task.end is not None
    assert finished_task.end > finished_task.start
    assert finished_task.input == task.input
