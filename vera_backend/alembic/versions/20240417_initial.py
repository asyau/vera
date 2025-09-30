"""initial

Revision ID: 20240417_initial
Revises:
Create Date: 2024-04-17 16:20:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20240417_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("team_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("assignedTo", sa.String(), nullable=True),
        sa.Column("dueDate", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("originalPrompt", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["assignedTo"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create timelines table
    op.create_table(
        "timelines",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("sentAt", sa.DateTime(), nullable=True),
        sa.Column("completedAt", sa.DateTime(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_companies_name", "companies", ["name"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_team_id", "users", ["team_id"])
    op.create_index("idx_teams_company_id", "teams", ["company_id"])
    op.create_index("idx_tasks_assignedTo", "tasks", ["assignedTo"])
    op.create_index("idx_timelines_task_id", "timelines", ["task_id"])


def downgrade():
    # Drop all tables in reverse order
    op.drop_table("timelines")
    op.drop_table("tasks")
    op.drop_table("users")
    op.drop_table("teams")
    op.drop_table("companies")
