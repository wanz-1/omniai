# OmniAI Version 2.0 — Technical Architecture Document

## 1. System Architecture Overview

```
                        ┌─────────────────────────────────┐
                        │         API Gateway (Kong)       │
                        │   Rate Limit · Auth · Routing    │
                        └──────────────┬──────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
     ┌────────▼────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
     │  Monolith API    │    │  Microservices    │    │  Real-time (WS)   │
     │  (v1 compatibility)│   │  (v2 new features)│    │  Voice/Video/Stream │
     └────────┬────────┘    └─────────┬─────────┘    └─────────┬─────────┘
              │                        │                        │
     ┌────────▼────────────────────────▼────────────────────────▼─────────┐
     │                       Message Queue (RabbitMQ/Redis)               │
     │          Task Queue · Event Bus · Webhook Dispatcher               │
     └────────┬────────────────────────┬────────────────────────┬─────────┘
              │                        │                        │
     ┌────────▼────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
     │  PostgreSQL 16  │    │  Vector DB (Qdrant)│    │  Object Store     │
     │  (relational)   │    │  (embeddings)      │    │  (S3/MinIO)       │
     └─────────────────┘    └───────────────────┘    └───────────────────┘
              │                        │                        │
     ┌────────▼────────────────────────▼────────────────────────▼─────────┐
     │                       AI Model Router                               │
     │   OpenAI · Anthropic · Groq · Replicate · ElevenLabs · Whisper     │
     │   Stable Diffusion · CLIP · Whisper · TTS · RTMP Streaming         │
     └────────────────────────────────────────────────────────────────────┘
```

## 2. Microservice Boundaries

| Service | Responsibility | DB | Scale |
|---------|--------------|-----|-------|
| **voice-service** | STT, TTS, real-time voice, WebRTC, phone integration | Redis streams | High (streaming) |
| **vision-service** | Image analysis, OCR, diagram parsing, screenshot AI | Vector DB | Medium |
| **video-service** | Video summarization, captioning, scene analysis, generation | Object store | High (file processing) |
| **agent-orchestrator** | Multi-agent collaboration, agent teams, consensus | PostgreSQL | High |
| **autonomous-biz** | Business manager, finance officer, ops, CS | PostgreSQL + Vector | Medium |
| **code-studio** | AI code generation, review, security scan, deploy | PostgreSQL | Medium |
| **marketplace-v2** | Listings, payments, reviews, analytics | PostgreSQL | Medium |
| **industry-solutions** | Per-vertical AI configs (edu, health, agri, tourism) | PostgreSQL | Low |
| **infra-manager** | Multi-region deployment, caching, DR, routing | Redis + Config | High |
| **notifications** | Email, SMS, push, webhooks | Redis | High |

## 3. Database Schema Additions (Phase 7-13)

### 3.1 Voice & Media Assets
```sql
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    agent_id UUID REFERENCES agent_profiles(id),
    status VARCHAR(20) DEFAULT 'active', -- active, ended, failed
    duration_ms INTEGER,
    recording_url TEXT,
    transcript JSONB,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE voice_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES voice_sessions(id),
    command_text TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT,
    executed BOOLEAN DEFAULT false,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    asset_type VARCHAR(20) NOT NULL, -- image, video, audio, document
    mime_type VARCHAR(100),
    storage_key TEXT NOT NULL,
    size_bytes BIGINT,
    width INT, height INT,
    duration_ms INT,
    thumbnail_key TEXT,
    ocr_text TEXT,
    ai_tags JSONB,
    embedding_id UUID, -- reference to vector store
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.2 Multi-Agent Collaboration
```sql
CREATE TABLE agent_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB, -- team composition, coordination strategy
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agent_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES agent_teams(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agent_profiles(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- lead, reviewer, executor
    priority INT DEFAULT 0,
    UNIQUE(team_id, agent_id)
);

CREATE TABLE agent_collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES agent_teams(id),
    task_id UUID REFERENCES agent_tasks(id),
    status VARCHAR(20) DEFAULT 'in_progress',
    strategy VARCHAR(50) DEFAULT 'sequential', -- sequential, parallel, debate, voting
    consensus_required BOOLEAN DEFAULT false,
    round INT DEFAULT 1,
    max_rounds INT DEFAULT 3,
    final_output JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE collaboration_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collaboration_id UUID REFERENCES agent_collaborations(id) ON DELETE CASCADE,
    from_agent_id UUID REFERENCES agent_profiles(id),
    to_agent_id UUID REFERENCES agent_profiles(id),
    message_type VARCHAR(50), -- proposal, review, approval, revision
    content JSONB,
    confidence FLOAT,
    round INT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.3 Autonomous Business
```sql
CREATE TABLE business_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    agent_id UUID REFERENCES agent_profiles(id),
    metric_type VARCHAR(50) NOT NULL, -- revenue, expense, cashflow, kpi
    metric_name VARCHAR(200),
    value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    period_start DATE,
    period_end DATE,
    source VARCHAR(100), -- stripe, manual, integration
    raw_data JSONB,
    recorded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE business_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    agent_id UUID REFERENCES agent_profiles(id),
    report_type VARCHAR(50), -- financial, operational, strategic
    title VARCHAR(300),
    content JSONB,
    insights JSONB,
    recommendations JSONB,
    generated_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.4 Code Studio
```sql
CREATE TABLE code_projects_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    language VARCHAR(50),
    framework VARCHAR(100),
    repo_url TEXT,
    deployment_url TEXT,
    template_id UUID REFERENCES marketplace_items(id),
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE code_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES code_projects_v2(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    generated_code TEXT,
    file_path VARCHAR(500),
    language VARCHAR(50),
    tokens_used INT,
    model VARCHAR(100),
    reviewed BOOLEAN DEFAULT false,
    review_result JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE code_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID REFERENCES code_generations(id) ON DELETE CASCADE,
    reviewer_type VARCHAR(20), -- ai, human
    status VARCHAR(20), -- approved, changes_requested, rejected
    issues JSONB,
    suggestions JSONB,
    security_flags JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.5 Industry Solutions
```sql
CREATE TABLE industry_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    industry VARCHAR(50) NOT NULL, -- education, healthcare, agriculture, tourism, ngo
    sub_category VARCHAR(100),
    config JSONB,
    active_features JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE industry_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES industry_profiles(id) ON DELETE CASCADE,
    metric_key VARCHAR(100) NOT NULL,
    metric_value JSONB,
    recorded_at TIMESTAMPTZ DEFAULT now()
);
```

## 4. AI Model Router Configuration

```yaml
# config/ai_router.yml
models:
  chat:
    primary: openai/gpt-4o
    fallback: anthropic/claude-3.5-sonnet
    cost_optimized: groq/llama-3.3-70b
  vision:
    primary: openai/gpt-4o-vision
    fallback: anthropic/claude-3.5-sonnet-vision
    local: ollama/llava
  voice_stt:
    primary: openai/whisper-1
    local: whisper.cpp
  voice_tts:
    primary: elevenlabs/multi-lingual-v2
    fallback: openai/tts-1
  voice_realtime:
    primary: deepgram/nova-2
    fallback: assemblyai/streaming
  image_generation:
    primary: stability-ai/sdxl-turbo
    fallback: openai/dall-e-3
    local: comfyui
  video_summary:
    primary: anthropic/claude-3.5-sonnet-video
    fallback: google/gemini-1.5-pro-video
  embeddings:
    primary: openai/text-embedding-3-large
    local: sentence-transformers/all-MiniLM-L6-v2
  code:
    primary: anthropic/claude-3.5-sonnet-code
    fallback: openai/gpt-4o-code
    local: ollama/codellama

routing:
  strategy: latency_first
  cost_budget_monthly: 1000  # max $ spend before fallback to cheaper models
  latency_threshold_ms: 2000
  enable_local_fallback: true
  cache_embeddings: true
  cache_prefix_hits: true
```

## 5. API Routes — Version 2.0 Additions

### Voice API (`/api/v2/voice`)
```
POST   /sessions                    — Start voice session
POST   /sessions/:id/transcribe     — Real-time STT (WebSocket)
POST   /sessions/:id/speak          — TTS response
WS     /sessions/:id/stream         — Bidirectional real-time audio
POST   /commands                    — Voice command interpretation
GET    /sessions                    — Session history
DELETE /sessions/:id                — End session
```

### Vision API (`/api/v2/vision`)
```
POST   /analyze                     — Analyze image (file + prompt)
POST   /ocr                         — OCR from image
POST   /scan                        — Document scan with auto-crop
POST   /diagram                     — Diagram interpretation
POST   /screenshot                  — Screenshot analysis
GET    /assets/:id                  — Get asset metadata
```

### Video API (`/api/v2/video`)
```
POST   /summarize                   — Video summarization
POST   /captions                    — Auto-caption generation
POST   /analyze                     — Scene analysis
POST   /generate                    — Video generation (script → video)
```

### Multi-Agent API (`/api/v2/agents`)
```
POST   /teams                       — Create agent team
GET    /teams                       — List agent teams
POST   /teams/:id/agents            — Add agent to team
POST   /teams/:id/collaborate       — Start collaboration on task
GET    /collaborations/:id          — Get collaboration status
POST   /collaborations/:id/message  — Send inter-agent message
```

### Autonomous Business API (`/api/v2/business`)
```
POST   /metrics                     — Record business metric
GET    /metrics/dashboard           — Business dashboard data
POST   /reports/generate            — Generate business report
GET    /reports                     — List reports
POST   /forecast                    — Financial forecasting
```

### Code Studio API (`/api/v2/code`)
```
POST   /projects                    — Create code project
GET    /projects                    — List projects
POST   /projects/:id/generate       — AI code generation
POST   /projects/:id/review         — Code review
POST   /projects/:id/security       — Security scan
POST   /projects/:id/deploy         — Deploy application
POST   /projects/:id/github         — Push to GitHub
```

### Industry API (`/api/v2/industry`)
```
POST   /profile                     — Set industry profile
GET    /profile                     — Get industry config
GET    /solutions                   — List industry solutions
POST   /solutions/:id/activate      — Activate industry feature
```

### Marketplace V2 API (`/api/v2/marketplace`)
```
POST   /listings                    — Publish solution
GET    /listings                    — Browse marketplace
POST   /listings/:id/purchase       — Purchase with auto-install
POST   /listings/:id/review         — Leave review
GET    /recommendations             — AI-powered recommendations
```

## 6. Real-Time Architecture

```
┌──────────────┐     WebSocket/WebRTC     ┌──────────────────┐
│   Frontend    │◄────────────────────────►│  WebSocket GW    │
│  (Next.js)   │                          │  (Socket.IO)      │
└──────────────┘                          └────────┬─────────┘
                                                   │
                    ┌───────────────────────────────┼───────────────┐
                    │                               │               │
          ┌─────────▼─────────┐         ┌───────────▼───────────┐   │
          │  Voice Stream      │         │  Agent Collaboration │   │
          │  (Audio Chunks)    │         │  (Events + Messages) │   │
          └─────────┬─────────┘         └───────────┬───────────┘   │
                    │                               │               │
          ┌─────────▼─────────┐         ┌───────────▼───────────┐   │
          │   Deepgram/       │         │   Redis Pub/Sub       │   │
          │   Whisper STT     │         │   Agent Events        │   │
          └─────────┬─────────┘         └───────────┬───────────┘   │
                    │                               │               │
          ┌─────────▼─────────┐         ┌───────────▼───────────┐   │
          │  ElevenLabs/      │         │   PostgreSQL          │   │
          │  OpenAI TTS       │         │   Persistence         │   │
          └───────────────────┘         └───────────────────────┘   │
                                                                   │
          ┌─────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────┐
│  Background Workers  │
│  (Celery / Temporal) │
│  Video Processing    │
│  Batch AI Tasks      │
│  Report Generation   │
└──────────────────────┘
```

## 7. Service Mesh & Communication

```
Service-to-service communication:
- REST/gRPC: Synchronous queries, CRUD
- RabbitMQ: Async task delegation, event-driven workflows
- Redis Pub/Sub: Real-time agent collaboration messages
- gRPC streams: Voice audio frames, video frames

gRPC Service Definitions (key services):

service VoiceService {
    rpc TranscribeStream(stream AudioChunk) returns (stream TranscriptionResult);
    rpc Synthesize(SynthesisRequest) returns (stream AudioChunk);
    rpc ProcessCommand(VoiceCommand) returns (CommandResult);
}

service AgentOrchestrator {
    rpc StartCollaboration(CollaborationRequest) returns (stream CollaborationEvent);
    rpc SubmitAgentResult(AgentResult) returns (Ack);
    rpc GetTeamStatus(TeamQuery) returns (TeamStatus);
}

service MediaProcessor {
    rpc AnalyzeImage(ImageRequest) returns (ImageAnalysis);
    rpc SummarizeVideo(VideoRequest) returns (VideoSummary);
    rpc OCRDocument(DocumentRequest) returns (OCRResult);
}
```

## 8. Infrastructure & Scaling

```
┌────────────────────────────────────────────────────────────────┐
│                   Global Load Balancer                         │
│           (Cloudflare / AWS Global Accelerator)                │
└──────────────┬────────────────────────────────┬────────────────┘
               │                                │
    ┌──────────▼──────────┐          ┌──────────▼──────────┐
    │   Region: US-East   │          │   Region: EU-West   │
    │   ┌──────────────┐  │          │   ┌──────────────┐  │
    │   │ K8s Cluster  │  │          │   │ K8s Cluster  │  │
    │   │ (3-10 nodes) │  │          │   │ (3-10 nodes) │  │
    │   └──────┬───────┘  │          │   └──────┬───────┘  │
    │          │          │          │          │          │
    │   ┌──────▼───────┐  │          │   ┌──────▼───────┐  │
    │   │ PostgreSQL   │  │          │   │ PostgreSQL   │  │
    │   │ (Primary)    │  │          │   │ (Replica)    │  │
    │   └──────────────┘  │          │   └──────────────┘  │
    └─────────────────────┘          └─────────────────────┘

Data Residency:
- User data stored in nearest region (GDPR enforced for EU)
- Read replicas in all active regions
- Cross-region async replication for disaster recovery

Caching Strategy:
- Redis: Session data, rate limits, real-time state
- CDN: Static assets, video thumbnails, marketplace images
- AI response cache: Deduplicate identical prompts
- Embedding cache: LRU with 1M entry limit
```

## 9. Model Inference Pipeline

```
┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  Request   │────►│  AI Router   │────►│  Model Exec  │
│  Queue     │     │  (Priority)  │     │  (Worker)    │
└────────────┘     └──────┬───────┘     └──────┬───────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐     ┌──────────────┐
                   │  Router      │     │  Response    │
                   │  Logic:      │     │  Cache       │
                   │  - Cost      │     │  (Redis)     │
                   │  - Latency   │     └──────────────┘
                   │  - Capacity  │
                   │  - Fallback  │
                   └──────┬───────┘
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Cloud AI    │ │  Local AI    │ │  Specialized     │
│  (OpenAI,    │ │  (Ollama,    │ │  (ElevenLabs,    │
│   Anthropic) │ │   vLLM)      │ │   Deepgram,      │
└──────────────┘ └──────────────┘ └──────────────────┘
```

## 10. Development Phases

### Phase 7 — Multimodal (Weeks 1-4)
- voice-service: WebRTC + Deepgram STT + ElevenLabs TTS
- vision-service: GPT-4o Vision + OCR + image analysis
- video-service: Claude 3.5 video + captioning
- Frontend: Voice recorder component, image upload with AI overlay

### Phase 8 — Autonomous Business (Weeks 5-8)
- Business metrics collector (Stripe + manual)
- AI Business Manager agent template
- AI Finance Officer with forecasting
- AI Ops Manager with workflow tracking
- AI CSM with customer sentiment analysis

### Phase 9 — Agent Network (Weeks 9-10)
- Agent team CRUD
- Collaboration engine (sequential, debate, voting)
- Inter-agent messaging with consensus
- Multi-agent dashboard

### Phase 10 — Code Studio (Weeks 11-12)
- Monaco Editor integration
- AI code generation with file tree
- Code review with security scanning
- One-click deploy (Vercel + Docker)

### Phase 11 — Marketplace V2 (Week 12-13)
- Global listing categories (industry-specific)
- AI-powered recommendations
- Purchase → auto-install flow
- Reviews and ratings

### Phase 12 — Industry Solutions (Weeks 13-14)
- Industry profile configuration
- Per-vertical agent templates (Education, Healthcare, Agri, Tourism, NGO)
- Industry-specific analytics dashboards

### Phase 13 — Global Scale (Weeks 14-16)
- Multi-region Kubernetes deployment
- Cross-region replication
- Disaster recovery automation
- Data residency controls
- Enterprise API with SLA monitoring

## 11. Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| API Gateway | Kong / AWS API Gateway |
| WebSocket | Socket.IO + Redis adapter |
| Real-time Audio | WebRTC + Deepgram/Whisper |
| Service Mesh | gRPC + RabbitMQ |
| Containers | Docker + Kubernetes (EKS/GKE) |
| Relational DB | PostgreSQL 16 + TimescaleDB (time-series) |
| Vector DB | Qdrant (self-hosted) |
| Cache | Redis 7 (cluster mode) |
| Object Storage | MinIO / S3 |
| AI Inference | vLLM + Ollama + Cloud APIs |
| Voice AI | Deepgram / ElevenLabs / Whisper |
| Video AI | Claude 3.5 Video / Gemini 1.5 |
| CI/CD | GitHub Actions + ArgoCD |
| Monitoring | Grafana + Prometheus + Sentry |
| IaC | Terraform + Helm Charts |

## 12. Security & Compliance

```
Phase 13 additions:
- Data residency: Configurable per-org data region
- Encryption: AES-256 at rest, TLS 1.3 in transit
- Audit: All AI interactions logged with full trace
- Access: Fine-grained RBAC per microservice
- Compliance: SOC 2 Type II, GDPR, HIPAA (healthcare)
- Secrets: Vault + Kubernetes External Secrets
- Network: Service mesh mTLS, network policies
```
