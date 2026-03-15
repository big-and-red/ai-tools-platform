"""seed_code_review_tool

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text("""
            INSERT INTO tools (id, name, description, tool_type, credit_cost_base, is_active)
            SELECT gen_random_uuid(),
                   'Code Reviewer',
                   'Paste any code snippet and get a structured review with severity-rated issues, line references, and actionable fixes. Supports all major languages.',
                   'code_review',
                   50,
                   true
            WHERE NOT EXISTS (
                SELECT 1 FROM tools WHERE tool_type = 'code_review'
            )
        """)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM tools WHERE tool_type = 'code_review'")
    )
