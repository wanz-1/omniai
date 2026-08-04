# OmniAI API Documentation

## Overview

OmniAI provides a comprehensive REST API for AI-powered document processing, website generation, chatbot management, code assistance, agent orchestration, and third-party integrations.

- **Base URL**: `https://api.omniai.example.com/api/v1`
- **Authentication**: JWT Bearer token or API key
- **Content-Type**: `application/json`

## Authentication

### Obtain JWT Token
```
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Refresh Token
```
POST /auth/refresh
Authorization: Bearer <refresh_token>
Response: { "access_token": "...", "expires_in": 900 }
```

### Using API Key
```
GET /v1/resource
X-API-Key: omni_<your-api-key>
```

## Core Endpoints

### Documents
| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents` | Create document |
| GET | `/documents` | List documents |
| GET | `/documents/{id}` | Get document |
| PUT | `/documents/{id}` | Update document |
| DELETE | `/documents/{id}` | Delete document |
| POST | `/documents/{id}/humanize` | Humanize document text |
| POST | `/documents/{id}/summarize` | Summarize document |
| POST | `/documents/{id}/translate` | Translate document |
| POST | `/documents/{id}/grammar` | Check grammar |
| GET | `/documents/{id}/versions` | List versions |
| POST | `/documents/{id}/versions/{vid}/restore` | Restore version |

### Websites
| Method | Path | Description |
|--------|------|-------------|
| POST | `/websites/generate` | Generate website from prompt |
| POST | `/websites/{id}/publish` | Publish website |
| POST | `/websites/{id}/deploy` | Deploy to hosting |
| POST | `/websites/{id}/branding` | Generate branding |
| GET | `/websites/{id}/export` | Export site files |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat/sessions` | Create chat session |
| POST | `/chat/sessions/{id}/messages` | Send message (streaming) |
| GET | `/chat/sessions/{id}/messages` | Get message history |
| PUT | `/chat/sessions/{id}/title` | Update session title |

### Bots
| Method | Path | Description |
|--------|------|-------------|
| POST | `/bots` | Create bot |
| POST | `/bots/{id}/train` | Train bot |
| POST | `/bots/{id}/test` | Test bot |
| POST | `/bots/{id}/deploy` | Deploy bot |
| GET | `/bots/{id}/embed` | Get embed code |

### Code Studio
| Method | Path | Description |
|--------|------|-------------|
| POST | `/code/generate` | Generate code |
| POST | `/code/explain` | Explain code |
| POST | `/code/review` | Review code |
| POST | `/code/debug` | Debug code |

### Agent System
| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents` | Create agent |
| GET | `/agents` | List agents |
| POST | `/agents/{id}/chat` | Chat with agent |
| POST | `/agents/{id}/execute` | Execute task |
| POST | `/agents/orchestrate` | Orchestrate multi-agent task |
| POST | `/agents/teams` | Create agent team |
| POST | `/agents/memory` | Store agent memory |
| GET | `/agents/memory/search` | Search agent memory |

### Connector Platform
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v5/connector/definitions` | List connector definitions |
| POST | `/v5/connector/install` | Install connector |
| GET | `/v5/connector/integrations` | List integrations |
| GET | `/v5/connector/oauth/authorize/{id}` | Get OAuth URL |
| POST | `/v5/connector/oauth/callback/{id}` | Handle OAuth callback |
| POST | `/v5/connector/oauth/refresh/{id}` | Refresh OAuth token |
| POST | `/v5/connector/sync/run/{id}` | Run sync |
| POST | `/v5/connector/query` | Execute connector action |
| POST | `/v5/connector/webhooks/register` | Register webhook |
| POST | `/v5/connector/webhooks/deliver/{id}` | Deliver webhook |
| POST | `/v5/connector/api-keys` | Create API key |
| GET | `/v5/connector/dashboard` | Connector dashboard |

### Governance
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v6/governance/prompts` | Create prompt |
| POST | `/v6/governance/prompts/{id}/versions` | Create version |
| POST | `/v6/governance/prompts/{id}/activate` | Activate version |
| POST | `/v6/governance/prompts/{id}/rollback` | Rollback version |
| POST | `/v6/governance/evaluate` | Evaluate AI response |
| GET | `/v6/governance/quality/{model}` | Get quality report |
| POST | `/v6/governance/hallucination/check` | Check for hallucinations |
| POST | `/v6/governance/feedback` | Submit feedback |
| POST | `/v6/governance/audit/decisions` | Record AI decision |

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed",
    "correlation_id": "req-abc-123",
    "timestamp": "2024-07-30T12:00:00Z"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `not_found` | 404 | Resource not found |
| `auth_error` | 401 | Authentication failed |
| `forbidden` | 403 | Permission denied |
| `validation_error` | 422 | Invalid input |
| `ai_service_error` | 502 | AI provider error |
| `provider_overloaded` | 503 | AI provider overloaded |
| `provider_rate_limit` | 429 | AI provider rate limited |
| `insufficient_credits` | 402 | Not enough credits |
| `rate_limit_exceeded` | 429 | Request rate limit hit |

## Rate Limiting

- **Default**: 1000 requests per 60 seconds per organization
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Status on limit**: 429 Too Many Requests

## Streaming

Chat and agent endpoints support Server-Sent Events (SSE) for streaming responses:

```
GET /chat/sessions/{id}/messages/stream
Accept: text/event-stream

data: {"type": "token", "content": "Hello"}
data: {"type": "token", "content": " world"}
data: {"type": "done"}
```

## Webhooks

Connector platform supports outgoing webhooks for event notifications. Each webhook delivery includes:

- **Signature**: `X-OmniAI-Signature` header (HMAC-SHA256)
- **Payload**: `{"event_id": "...", "event_type": "...", "payload": {...}}`
- **Retry**: Up to 3 attempts with exponential backoff (5s, 30s, 120s)
