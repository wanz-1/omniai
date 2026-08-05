import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    system_prompt: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    industry: Optional[str] = None
    tone: Optional[str] = None
    knowledge_base_config: Optional[dict] = None
    widget_config: Optional[dict] = None


class BotUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    is_active: Optional[bool] = None
    industry: Optional[str] = None
    tone: Optional[str] = None
    knowledge_base_config: Optional[dict] = None
    widget_config: Optional[dict] = None


class BotTrainRequest(BaseModel):
    files: Optional[list[str]] = None
    urls: Optional[list[str]] = None
    text: Optional[str] = None


class BotTestRequest(BaseModel):
    message: str = Field(..., min_length=1)


class BotTestResponse(BaseModel):
    reply: str
    latency_ms: int
    tokens_used: int


class BotDeployRequest(BaseModel):
    channels: list[str]


class BotChannelConfigRequest(BaseModel):
    webhook_url: Optional[str] = None
    api_token: Optional[str] = None
    config: Optional[dict] = None


class BotResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str
    temperature: float
    industry: Optional[str] = None
    tone: Optional[str] = None
    is_active: bool
    deployment_url: Optional[str] = None
    knowledge_base_config: Optional[dict] = None
    widget_config: Optional[dict] = None
    project_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotConversationResponse(BaseModel):
    id: uuid.UUID
    bot_id: uuid.UUID
    session_id: str
    channel: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BotMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BotAnalyticsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    avg_satisfaction: Optional[float] = None
    top_intents: Optional[list[dict]] = None
    active_users_today: int = 0
    resolution_rate: float = 0.0
    daily_activity: Optional[list[dict]] = None


class BotEmbedRequest(BaseModel):
    theme: dict = {"primary": "#2563EB", "position": "right", "greeting": "Hello! How can I help?"}


class BotEmbedResponse(BaseModel):
    embed_code: str
    widget_url: str
    config: dict
