"""Populate DB

Revision ID: e4715258ca97
Revises: f9544ce8dde2
Create Date: 2024-05-01 20:09:16.317958

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import Sequence as SASequence


# revision identifiers, used by Alembic.
revision: str = 'e4715258ca97'
down_revision: Union[str, None] = '6edcce752953'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_table = sa.sql.table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('tg_id', sa.Integer(), nullable=True),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('deactivated', sa.Boolean(), nullable=True),
    )
    user_data = [
        {
            "id": 1,
            "email": "user1@example.com",
            "tg_id": None,
            "password": "$2b$12$nfBxd.wC6Ho5eNMghQeTH.YzWi1NLL.RAmhSf09iPCd5AETCiE4MS",
            "deactivated": None
        },
        {
            "id": 2,
            "email": "user2@example.com",
            "tg_id": None,
            "password": "$2b$12$oIG4vJxZdFLGlZSNqOdjEevfzvzBC5TtJ0e5v8CS7a27pAFxvOx.a",
            "deactivated": None
        }
    ]
    op.bulk_insert(user_table, user_data)
    op.execute("ALTER SEQUENCE user_id_seq RESTART WITH 3")

    account_table = sa.sql.table(
        'account',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Numeric(), nullable=False, default=0),
    )
    account_data = [
        {
            "id": 1,
            "user_id": 1,
            "balance": 100,
        },
        {
            "id": 2,
            "user_id": 2,
            "balance": 0,
        }
    ]
    op.bulk_insert(account_table, account_data)
    op.execute("ALTER SEQUENCE account_id_seq RESTART WITH 3")

    transaction_table = sa.sql.table(
        'transaction',
        sa.Column('id', sa.Integer(),  primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column(
            'type',
            sa.Enum('dep', 'wdr', name='transactiontype'),
            nullable=False
        ),
        sa.Column('amount', sa.Numeric(), nullable=False),
    )
    transaction_data = [
        {
            "id": 1,
            "user_id": 1,
            "timestamp": "2024-04-26 06:42:23.524345",
            "type": "dep",
            "amount": 100,
        },
    ]
    op.bulk_insert(transaction_table, transaction_data)
    op.execute("ALTER SEQUENCE transaction_id_seq RESTART WITH 2")

    service_table = sa.sql.table(
        'service',
        sa.Column('name', sa.String(), primary_key=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column(
            'pricing_type',
            sa.Enum('fixed', 'token', name='servicepricingtype'),
            nullable=False
        ),
        sa.Column('price', sa.Numeric(), nullable=False),
    )
    service_data = [
        {
            "name": "dummy",
            "description": "Dummy model",
            "pricing_type": "fixed",
            "price": 5,
        },
        {
            "name": "real_estate",
            "description": "Real estate price prediction",
            "pricing_type": "fixed",
            "price": 10,
        }
    ]
    op.bulk_insert(service_table, service_data)


def downgrade() -> None:
    op.execute("DELETE FROM transaction")
    op.execute('DELETE FROM "user"')
    op.execute('DELETE FROM service')
