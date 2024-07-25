import os
from datetime import datetime
from typing import Callable
from typing import Tuple
from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.core.db
from app.core.db import Base
from app.core.deps import get_db
from app.core.deps import get_cur_user_from_cookie
from app.core.deps import get_rmq
from app.main import app
from app.schemas import User


@pytest.fixture()
def session() -> Tuple[TestClient, Session]:
    engine = create_engine(
        f"sqlite:///{os.getenv('TEST_DB_FILE')}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def override_session(session: Session):

    def get_session_override():
        return session

    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client, session
    app.dependency_overrides.clear()


@pytest.fixture()
def override_get_auth_user() -> Tuple[TestClient, Callable]:

    def override(user: User):
        app.dependency_overrides[get_cur_user_from_cookie] = lambda: user

    client = TestClient(app)
    yield client, override
    app.dependency_overrides.clear()


@pytest.fixture()
def override_get_rmq():

    def get_rmq_override():
        return session

    app.dependency_overrides[get_rmq] = lambda: MagicMock()
    client = TestClient(app)
    yield client, session
    app.dependency_overrides.clear()


@pytest.fixture()
def fill_tables(request, override_session) -> Tuple[TestClient, Session]:
    client, session = override_session
    marker = request.node.get_closest_marker("fixt_data")
    if marker is None:
        return client, session

    user_data = marker.args[0].get('user_data', [])
    if user_data:
        user_table = sa.sql.table(
            'user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('password', sa.String(), nullable=False),
            sa.Column('deactivated', sa.Boolean(), nullable=True),
        )
        session.execute(insert(user_table), user_data)

    transaction_data = marker.args[0].get('transaction_data', [])
    if transaction_data:
        for trx in transaction_data:
            trx["timestamp"] = datetime.fromisoformat(trx["timestamp"])
        transaction_table = sa.sql.table(
            'transaction',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('type', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(), nullable=False),
        )
        session.execute(insert(transaction_table), transaction_data)

    account_data = marker.args[0].get('account_data', [])
    if account_data:
        account_table = sa.sql.table(
            'account',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('balance', sa.Numeric(), nullable=False, default=0),
        )
        session.execute(insert(account_table), account_data)

    service_data = marker.args[0].get('service_data', [])
    if service_data:
        service_table = sa.sql.table(
            'service',
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('pricing_type', sa.Integer(), nullable=False),
            sa.Column('price', sa.Numeric(), nullable=False),
        )
        session.execute(insert(service_table), service_data)

    return client, session
