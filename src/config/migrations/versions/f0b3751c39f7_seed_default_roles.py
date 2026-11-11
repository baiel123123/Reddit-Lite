"""seed default roles

Revision ID: f0b3751c39f7
Revises: c9b6539750af
Create Date: 2026-11-11 14:42:19.829325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0b3751c39f7'
down_revision: Union[str, None] = 'c9b6539750af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )

    op.bulk_insert(
        roles,
        [
            {"id": 1, "name": "user"},
            {"id": 2, "name": "admin"},
            {"id": 3, "name": "super_admin"},
        ],
    )
    
    op.execute("""
        SELECT setval(
            pg_get_serial_sequence('roles', 'id'),
            (SELECT MAX(id) FROM roles)
        );
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM roles
        WHERE id IN (1, 2, 3);
    """)