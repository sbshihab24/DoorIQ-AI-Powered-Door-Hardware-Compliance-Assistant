"""add lead memory context

Revision ID: 20260510_0005
Revises: 20260505_0004
Create Date: 2026-05-10 00:00:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260510_0005"
down_revision: str | None = "20260505_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("chat_sessions", sa.Column("lead_name", sa.String(), nullable=True))
    op.add_column("chat_sessions", sa.Column("project_context", sa.JSON(), nullable=True))
    if bind.dialect.name != "sqlite":
        op.alter_column("leads", "email", existing_type=sa.String(), nullable=True)
        op.alter_column("leads", "phone", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column("leads", "phone", existing_type=sa.String(), nullable=False)
        op.alter_column("leads", "email", existing_type=sa.String(), nullable=False)
    op.drop_column("chat_sessions", "project_context")
    op.drop_column("chat_sessions", "lead_name")
