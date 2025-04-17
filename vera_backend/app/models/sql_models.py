from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(String, primary_key=True, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    sentAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="timeline")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    assignedTo = Column(String, ForeignKey("users.id"))
    dueDate = Column(DateTime, nullable=True)
    status = Column(String)
    description = Column(String)
    originalPrompt = Column(String)

    timeline = relationship("Timeline", uselist=False, back_populates="task")
    assigned_user = relationship("User", back_populates="tasks")


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    teams = relationship("Team", back_populates="company")

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    company_id = Column(String, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="teams")
    users = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)  # 'employee' or 'supervisor'
    team_id = Column(String, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="users")
    tasks = relationship("Task", back_populates="assigned_user")
