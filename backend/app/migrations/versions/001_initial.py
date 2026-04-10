"""Initial migration: create users, user_interactions, user_ratings tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable uuid-ossp extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BIGINT(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("interests", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("age_preferences", sa.Integer(), nullable=True),
        sa.Column("gender_preferences", sa.String(), nullable=True),
        sa.Column("interests_preferences", sa.String(), nullable=True),
        sa.Column("city_preferences", sa.String(), nullable=True),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.Column("referal_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["referal_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("telegram_id"),
    )

    op.create_table(
        "user_ratings",
        sa.Column("telegram_id", sa.BIGINT(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("telegram_id"),
    )

    op.create_table(
        "user_interactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("requester_telegram_id", sa.BIGINT(), nullable=False),
        sa.Column("responser_telegram_id", sa.BIGINT(), nullable=False),
        sa.Column("is_like", sa.BOOLEAN(), nullable=False),
        sa.Column("is_checked", sa.BOOLEAN(), nullable=True),
        sa.ForeignKeyConstraint(
            ["requester_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.ForeignKeyConstraint(
            ["responser_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_telegram_id", "responser_telegram_id"),
    )


def downgrade() -> None:
    op.drop_table("user_interactions")
    op.drop_table("user_ratings")
    op.drop_table("users")
