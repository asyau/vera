import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Fix the DATABASE_URL format - it should be postgresql:// not postgres.
# Also, the password should not be in square brackets
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.aphnekdbxvzcofzzxghu:Virastartupsok@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

logger = logging.getLogger(__name__)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    try:
        logger.info("Resetting database...")

        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all tables")

        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Created all tables")

        logger.info("Database reset completed successfully")

    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise


def init_database():
    """Initialize the database with tables."""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def check_database_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
