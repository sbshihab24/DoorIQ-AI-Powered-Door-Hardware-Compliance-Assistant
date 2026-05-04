"""use pgvector for document chunk embeddings

Revision ID: 20260505_0004
Revises: 20260503_0003
Create Date: 2026-05-05 00:00:00

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "20260505_0004"
down_revision: str | None = "20260503_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.alter_column(
            "document_chunks",
            "embedding",
            existing_type=sa.JSON(),
            type_=Vector(),
            postgresql_using="embedding::text::vector",
            nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column(
            "document_chunks",
            "embedding",
            existing_type=Vector(),
            type_=sa.JSON(),
            postgresql_using="embedding::text::json",
            nullable=True,
        )
