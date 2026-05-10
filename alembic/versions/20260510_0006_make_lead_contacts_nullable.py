"""make lead contacts nullable

Revision ID: 20260510_0006
Revises: 20260510_0005
Create Date: 2026-05-10 00:00:01

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260510_0006"
down_revision: str | None = "20260510_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("leads") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("phone", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("leads") as batch_op:
        batch_op.alter_column("phone", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("email", existing_type=sa.String(), nullable=False)
