from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


# Base Models
class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    company_profile: Optional[Dict[str, Any]] = None


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    company_id: UUID


class TeamBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: Optional[UUID] = None
    company_id: UUID
    supervisor_id: Optional[UUID] = None


class UserBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)
    role: str = Field(..., max_length=50)
    company_id: UUID
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    preferences: Optional[Dict[str, Any]] = None


class TaskBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", max_length=50)
    assigned_to: Optional[UUID] = None
    due_date: Optional[datetime] = None
    original_prompt: Optional[str] = None
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    priority: str = Field(default="medium", max_length=50)


class ConversationBase(BaseModel):
    type: str = Field(..., max_length=50)
    participant_ids: List[UUID]
    project_id: Optional[UUID] = None
    team_id: Optional[UUID] = None


class MessageBase(BaseModel):
    conversation_id: UUID
    content: str
    type: str = Field(..., max_length=50)
    is_read: bool = False


class DocumentBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    storage_path: str
    project_id: Optional[UUID] = None
    team_id: Optional[UUID] = None


class DocumentChunkBase(BaseModel):
    document_id: UUID
    chunk_text: str
    chunk_order: int
    embedding: List[float]  # Vector representation


class MemoryVectorBase(BaseModel):
    user_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    content: str
    embedding: List[float]  # Vector representation
    source_type: Optional[str] = Field(None, max_length=100)
    source_id: Optional[UUID] = None


class NotificationBase(BaseModel):
    user_id: UUID
    type: str = Field(..., max_length=100)
    message: str
    read_status: bool = False
    related_entity_type: Optional[str] = Field(None, max_length=100)
    related_entity_id: Optional[UUID] = None


class IntegrationBase(BaseModel):
    company_id: UUID
    integration_type: str = Field(..., max_length=100)
    config: Dict[str, Any]
    enabled: bool = True


# Create Models
class CompanyCreate(CompanyBase):
    pass


class ProjectCreate(ProjectBase):
    pass


class TeamCreate(TeamBase):
    pass


class UserCreate(UserBase):
    pass


class TaskCreate(TaskBase):
    created_by: UUID


class ConversationCreate(ConversationBase):
    pass


class MessageCreate(MessageBase):
    sender_id: UUID


class DocumentCreate(DocumentBase):
    uploaded_by: UUID


class DocumentChunkCreate(DocumentChunkBase):
    pass


class MemoryVectorCreate(MemoryVectorBase):
    pass


class NotificationCreate(NotificationBase):
    pass


class IntegrationCreate(IntegrationBase):
    pass


# Response Models
class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    company: Optional[CompanyResponse] = None

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class UserSummary(BaseModel):
    id: UUID
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class TeamResponse(TeamBase):
    id: UUID
    created_at: datetime
    project: Optional[ProjectResponse] = None
    company: Optional[CompanyResponse] = None
    supervisor: Optional[UserSummary] = None

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    company: Optional[CompanyResponse] = None
    team: Optional[TeamResponse] = None
    project: Optional[ProjectResponse] = None
    # Removed supervised_teams to avoid circular dependency

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class TaskResponse(TaskBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None
    creator: Optional[UserResponse] = None
    project: Optional[ProjectResponse] = None
    conversation: Optional["ConversationResponse"] = None

    class Config:
        from_attributes = True


class ConversationResponse(ConversationBase):
    id: UUID
    created_at: datetime
    last_message_at: datetime
    project: Optional[ProjectResponse] = None
    team: Optional[TeamResponse] = None
    messages: List["MessageResponse"] = []
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True


class MessageResponse(MessageBase):
    id: UUID
    sender_id: UUID
    timestamp: datetime
    sender: Optional[UserResponse] = None
    conversation: Optional[ConversationResponse] = None

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: UUID
    uploaded_by: UUID
    created_at: datetime
    processed: bool
    uploader: Optional[UserResponse] = None
    project: Optional[ProjectResponse] = None
    team: Optional[TeamResponse] = None
    chunks: List["DocumentChunkResponse"] = []

    class Config:
        from_attributes = True


class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime
    document: Optional[DocumentResponse] = None

    class Config:
        from_attributes = True


class MemoryVectorResponse(MemoryVectorBase):
    id: UUID
    timestamp: datetime
    user: Optional[UserResponse] = None
    company: Optional[CompanyResponse] = None

    class Config:
        from_attributes = True


class NotificationResponse(NotificationBase):
    id: UUID
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class IntegrationResponse(IntegrationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyResponse] = None

    class Config:
        from_attributes = True


# Update Models
class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    company_profile: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    project_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    preferences: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=50)
    completed_at: Optional[datetime] = None


class ConversationUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    participant_ids: Optional[List[UUID]] = None
    project_id: Optional[UUID] = None
    team_id: Optional[UUID] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None


class DocumentUpdate(BaseModel):
    file_name: Optional[str] = Field(None, max_length=255)
    file_type: Optional[str] = Field(None, max_length=100)
    processed: Optional[bool] = None


class NotificationUpdate(BaseModel):
    read_status: Optional[bool] = None


class IntegrationUpdate(BaseModel):
    integration_type: Optional[str] = Field(None, max_length=100)
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


# List Response Models
class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


class TeamListResponse(BaseModel):
    teams: List[TeamResponse]
    total: int


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int


class IntegrationListResponse(BaseModel):
    integrations: List[IntegrationResponse]
    total: int


# Forward references for circular imports
TeamResponse.model_rebuild()
ConversationResponse.model_rebuild()
MessageResponse.model_rebuild()
DocumentResponse.model_rebuild()
DocumentChunkResponse.model_rebuild()
