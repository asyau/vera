"""connect users to auth

Revision ID: a7f46c7547d7
Revises: 20240417_initial
Create Date: 2025-04-17 19:12:57.620054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7f46c7547d7'
down_revision: Union[str, None] = '20240417_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable RLS (Row Level Security)
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")

    # Create trigger function
    op.execute("""
    CREATE FUNCTION public.handle_new_user()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY definer SET search_path = ''
    AS $$
    BEGIN
      INSERT INTO public.users (id, first_name, last_name)
      VALUES (
        NEW.id,
        NEW.raw_user_meta_data ->> 'first_name',
        NEW.raw_user_meta_data ->> 'last_name'
      );
      RETURN NEW;
    END;
    $$;
    """)

    # Create trigger on auth.users
    op.execute("""
    CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

