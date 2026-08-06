from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    USER = "user"


class ProjectType(StrEnum):
    DOCUMENT = "document"
    WEBSITE = "website"
    BOT = "bot"
    CODE = "code"
    GENERAL = "general"


class DocumentType(StrEnum):
    TXT = "txt"
    MARKDOWN = "markdown"
    DOCX = "docx"
    PDF = "pdf"
    RTF = "rtf"


class Tone(StrEnum):
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"
    FRIENDLY = "friendly"
    PERSUASIVE = "persuasive"
    INSTRUCTIVE = "instructive"
    NARRATIVE = "narrative"
    TECHNICAL = "technical"
    SIMPLE = "simple"


class WebsiteFramework(StrEnum):
    HTML_CSS = "html-css"
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"


class WebsiteStyling(StrEnum):
    TAILWIND = "tailwind"
    BOOTSTRAP = "bootstrap"
    PLAIN_CSS = "plain-css"


class DeploymentStatus(StrEnum):
    DRAFT = "draft"
    BUILDING = "building"
    DEPLOYED = "deployed"
    FAILED = "failed"


class BotChannel(StrEnum):
    WEB = "web"
    API = "api"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    MESSENGER = "messenger"
    TEAMS = "teams"


class AIModelProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"
    VLLM = "vllm"


class OrganizationPlan(StrEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    EXPIRED = "expired"


class SubscriptionInterval(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class MarketplaceItemType(StrEnum):
    AGENT = "agent"
    TEMPLATE = "template"
    WORKFLOW = "workflow"
    TOOL = "tool"
    INTEGRATION = "integration"


class MarketplaceItemStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class IntegrationProvider(StrEnum):
    GOOGLE_WORKSPACE = "google_workspace"
    MICROSOFT_365 = "microsoft_365"
    SLACK = "slack"
    NOTION = "notion"
    TRELLO = "trello"
    ASANA = "asana"
    GITHUB = "github"
    GITLAB = "gitlab"
    DOCKER = "docker"
    STRIPE = "stripe"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    CUSTOM = "custom"


class IntegrationCategory(StrEnum):
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    BUSINESS = "business"
    PAYMENT = "payment"
    CUSTOM = "custom"


class MediaType(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class VoiceSessionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    FAILED = "failed"


class VideoJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceProvider(StrEnum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"
    GOOGLE_SPEECH = "google_speech"
    ELEVENLABS = "elevenlabs"
    AZURE_VOICE = "azure_voice"
    LOCAL_TTS = "local_tts"
    OPENAI_TTS = "openai_tts"


class NotificationType(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationCategory(StrEnum):
    DOCUMENT = "document"
    WEBSITE = "website"
    BOT = "bot"
    SYSTEM = "system"
    BILLING = "billing"
    TEAM = "team"
    GENERAL = "general"


class CreditTransactionType(StrEnum):
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"
    TRANSFER = "transfer"


class AgentStatus(StrEnum):
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class AgentTaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentToolType(StrEnum):
    WEB_SEARCH = "web_search"
    WEB_SCRAPE = "web_scrape"
    DOCUMENT_READ = "document_read"
    DOCUMENT_WRITE = "document_write"
    EMAIL = "email"
    CALENDAR = "calendar"
    DATABASE = "database"
    API_CALL = "api_call"
    FILE_SYSTEM = "file_system"
    CODE_EXECUTION = "code_execution"
    IMAGE_GENERATION = "image_generation"
    DATA_ANALYSIS = "data_analysis"
    CHART_CREATION = "chart_creation"
    SLACK = "slack"
    GITHUB = "github"
    GOOGLE_DRIVE = "google_drive"
    CRM = "crm"
    CUSTOM = "custom"


class WorkflowStepType(StrEnum):
    TRIGGER = "trigger"
    AI_DECISION = "ai_decision"
    CONDITION = "condition"
    ACTION = "action"
    TOOL_CALL = "tool_call"
    NOTIFICATION = "notification"
    API_CALL = "api_call"
    SUB_WORKFLOW = "sub_workflow"
    HUMAN_APPROVAL = "human_approval"
    DELAY = "delay"


class AgentTemplateCategory(StrEnum):
    FINANCE = "finance"
    HR = "hr"
    RESEARCH = "research"
    MARKETING = "marketing"
    PROJECT_MANAGEMENT = "project_management"
    PROCUREMENT = "procurement"
    LEGAL = "legal"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    CUSTOMER_SUPPORT = "customer_support"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    GENERAL = "general"
