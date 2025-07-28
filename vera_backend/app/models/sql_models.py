from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer, BigInteger, ARRAY, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, BIGINT
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.database import Base
import uuid

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    company_profile = Column(JSONB, nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="company")
    teams = relationship("Team", back_populates="company")
    users = relationship("User", back_populates="company")
    integrations = relationship("Integration", back_populates="company")
    memory_vectors = relationship("MemoryVector", back_populates="company")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="projects")
    teams = relationship("Team", back_populates="project")
    users = relationship("User", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    conversations = relationship("Conversation", back_populates="project")
    documents = relationship("Document", back_populates="project")

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="teams")
    company = relationship("Company", back_populates="teams")
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    users = relationship("User", foreign_keys="User.team_id", back_populates="team")
    conversations = relationship("Conversation", back_populates="team")
    documents = relationship("Document", back_populates="team")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=True)  # Added password field
    role = Column(String(50), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    preferences = Column(JSONB, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="users")
    team = relationship("Team", foreign_keys=[team_id], back_populates="users")
    project = relationship("Project", back_populates="users")
    supervised_teams = relationship("Team", foreign_keys="Team.supervisor_id", back_populates="supervisor")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    sent_messages = relationship("Message", back_populates="sender")
    uploaded_documents = relationship("Document", back_populates="uploader")
    notifications = relationship("Notification", back_populates="user")
    memory_vectors = relationship("MemoryVector", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_prompt = Column(Text, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    priority = Column(String(50), default="medium")

    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    project = relationship("Project", back_populates="tasks")
    conversation = relationship("Conversation", back_populates="tasks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String(50), nullable=False)
    participant_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    last_message_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="conversations")
    team = relationship("Team", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    tasks = relationship("Task", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(BIGINT, nullable=True)
    storage_path = Column(Text, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    # Relationships
    uploader = relationship("User", back_populates="uploaded_documents")
    project = relationship("Project", back_populates="documents")
    team = relationship("Team", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

class MemoryVector(Base):
    __tablename__ = "memory_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    source_type = Column(String(100), nullable=True)
    source_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="memory_vectors")
    company = relationship("Company", back_populates="memory_vectors")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    read_status = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    related_entity_type = Column(String(100), nullable=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    integration_type = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="integrations")
