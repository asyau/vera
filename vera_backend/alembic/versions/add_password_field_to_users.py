"""add password field to users

Revision ID: add_password_field_to_users
Revises: a7f46c7547d7
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_password_field_to_users"
down_revision: Union[str, None] = "a7f46c7547d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password column to users table
    op.add_column("users", sa.Column("password", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove password column from users table
    op.drop_column("users", "password")
