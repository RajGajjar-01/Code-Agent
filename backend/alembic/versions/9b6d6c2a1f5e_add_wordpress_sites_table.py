"""add_wordpress_sites_table

Revision ID: 9b6d6c2a1f5e
Revises: 581e9aaab449
Create Date: 2026-03-06 18:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b6d6c2a1f5e"
down_revision: Union[str, Sequence[str], None] = "581e9aaab449"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wordpress_sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("app_password_encrypted", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "base_url", name="uq_wordpress_sites_user_base_url"),
    )
    op.create_index("ix_wordpress_sites_user_id", "wordpress_sites", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_wordpress_sites_user_id", table_name="wordpress_sites")
    op.drop_table("wordpress_sites")
