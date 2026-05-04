"""add chat session context fields

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03 00:00:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260503_0003"
down_revision: str | None = "20260503_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("city", sa.String(), nullable=True))
    op.add_column("chat_sessions", sa.Column("is_new_construction", sa.Boolean(), nullable=True))
    op.add_column("chat_sessions", sa.Column("is_egress_path", sa.Boolean(), nullable=True))
    op.add_column("chat_sessions", sa.Column("fire_rating_required", sa.Boolean(), nullable=True))
    op.add_column("chat_sessions", sa.Column("accessibility_required", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_sessions", "accessibility_required")
    op.drop_column("chat_sessions", "fire_rating_required")
    op.drop_column("chat_sessions", "is_egress_path")
    op.drop_column("chat_sessions", "is_new_construction")
    op.drop_column("chat_sessions", "city")
