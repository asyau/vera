from app.database import Base, engine
from app.models.sql_models import Company, Project, Task, Team, User


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
