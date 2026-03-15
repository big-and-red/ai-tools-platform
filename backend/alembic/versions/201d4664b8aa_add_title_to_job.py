"""add_title_to_job

Revision ID: 201d4664b8aa
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 20:45:29.366175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '201d4664b8aa'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('title', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'title')
