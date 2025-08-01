"""post model fixed

Revision ID: efd8130dd3b5
Revises: 6e410cd77da1
Create Date: 2025-03-28 08:56:13.877624

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'efd8130dd3b5'
down_revision: Union[str, None] = '6e410cd77da1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('comments_post_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key(None, 'comments', 'posts', ['post_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.create_foreign_key('comments_post_id_fkey', 'comments', 'posts', ['post_id'], ['id'])
    # ### end Alembic commands ###
