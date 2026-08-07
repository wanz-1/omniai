import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    project_id: uuid.UUID | None = None
    system_prompt: str | None = None
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    industry: str | None = None
    tone: str | None = None
    knowledge_base_config: dict | None = None
    widget_config: dict | None = None


class BotUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    is_active: bool | None = None
    industry: str | None = None
    tone: str | None = None
    knowledge_base_config: dict | None = None
    widget_config: dict | None = None


class BotTrainRequest(BaseModel):
    files: list[str] | None = None
    urls: list[str] | None = None
    text: str | None = None


class BotTestRequest(BaseModel):
    message: str = Field(..., min_length=1)


class BotTestResponse(BaseModel):
    reply: str
    latency_ms: int
    tokens_used: int


class BotDeployRequest(BaseModel):
    channels: list[str]


class BotChannelConfigRequest(BaseModel):
    webhook_url: str | None = None
    api_token: str | None = None
    config: dict | None = None


class BotResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    system_prompt: str | None = None
    model: str
    temperature: float
    industry: str | None = None
    tone: str | None = None
    is_active: bool
    deployment_url: str | None = None
    knowledge_base_config: dict | None = None
    widget_config: dict | None = None
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotConversationResponse(BaseModel):
    id: uuid.UUID
    bot_id: uuid.UUID
    session_id: str
    channel: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotAnalyticsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    avg_satisfaction: float | None = None
    top_intents: list[dict] | None = None
    active_users_today: int = 0
    resolution_rate: float = 0.0
    daily_activity: list[dict] | None = None


class BotEmbedRequest(BaseModel):
    theme: dict = {"primary": "#2563EB", "position": "right", "greeting": "Hello! How can I help?"}


class BotEmbedResponse(BaseModel):
    embed_code: str
    widget_url: str
    config: dict
