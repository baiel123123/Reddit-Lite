"""status user model

Revision ID: 0642fd96dbcc
Revises: e8040f48fe2a
Create Date: 2025-04-11 23:33:23.248542

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0642fd96dbcc'
down_revision: Union[str, None] = 'e8040f48fe2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # создаём тип ENUM
    status_enum = sa.Enum('ACTIVE', 'BANNED', 'DELETED', name='userstatus')
    status_enum.create(op.get_bind())  # ЯВНО создаём тип в базе

    # добавляем колонку, используя уже созданный тип
    op.add_column(
        'users',
        sa.Column('status', status_enum, server_default='ACTIVE', nullable=False)
    )


def downgrade() -> None:
    # удаляем колонку
    op.drop_column('users', 'status')

    # удаляем ENUM тип
    status_enum = sa.Enum('ACTIVE', 'BANNED', 'DELETED', name='userstatus')
    status_enum.drop(op.get_bind())