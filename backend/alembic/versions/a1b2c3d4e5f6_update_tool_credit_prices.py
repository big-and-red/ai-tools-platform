"""update_tool_credit_prices

Revision ID: a1b2c3d4e5f6
Revises: 4f94ecba6b63
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "4f94ecba6b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PRICE_MAP = {
    "research_agent": (200, 5000),
    "code_review": (50, 500),
    "doc_qa": (100, 1000),
    "resume": (30, 300),
}


def upgrade() -> None:
    for tool_type, (new_price, _old) in PRICE_MAP.items():
        op.execute(
            sa.text(
                "UPDATE tools SET credit_cost_base = :price WHERE tool_type = :tt"
            ).bindparams(price=new_price, tt=tool_type)
        )
    op.alter_column("users", "credits_balance", server_default="500")


def downgrade() -> None:
    for tool_type, (_new, old_price) in PRICE_MAP.items():
        op.execute(
            sa.text(
                "UPDATE tools SET credit_cost_base = :price WHERE tool_type = :tt"
            ).bindparams(price=old_price, tt=tool_type)
        )
    op.alter_column("users", "credits_balance", server_default="10000")
