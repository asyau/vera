from app.database import engine, Base
from app.models.sql_models import Task, User, Company, Project, Team

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db() 