import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_connector_platform import (
    ConnectorDefinition, ConnectorIntegration, ConnectorLog,
)
from app.services.ai_service import ai_service

logger = logging.getLogger("omniai.connector.manager")

CONNECTOR_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "Google Drive",
        "connector_type": "google_drive",
        "category": "storage",
        "auth_type": "oauth2",
        "description": "Access and manage Google Drive files and folders",
        "icon": "drive",
        "actions": ["list_files", "read_file", "upload_file", "search", "create_folder"],
        "events": ["file_created", "file_modified", "file_deleted"],
    },
    {
        "name": "Gmail",
        "connector_type": "gmail",
        "category": "communication",
        "auth_type": "oauth2",
        "description": "Read, send, and manage Gmail messages",
        "icon": "gmail",
        "actions": ["list_emails", "send_email", "search_emails", "get_thread"],
        "events": ["email_received"],
    },
    {
        "name": "GitHub",
        "connector_type": "github",
        "category": "development",
        "auth_type": "oauth2",
        "description": "Manage repositories, issues, pull requests, and code",
        "icon": "github",
        "actions": ["list_repos", "create_issue", "list_issues", "get_readme", "search_code", "list_pull_requests"],
        "events": ["push", "pull_request", "issues", "star"],
    },
    {
        "name": "Slack",
        "connector_type": "slack",
        "category": "communication",
        "auth_type": "oauth2",
        "description": "Send messages, list channels, and manage Slack workspace",
        "icon": "slack",
        "actions": ["send_message", "list_channels", "get_channel_history", "list_users"],
        "events": ["message_received", "channel_created", "user_joined"],
    },
    {
        "name": "Microsoft 365",
        "connector_type": "microsoft_365",
        "category": "productivity",
        "auth_type": "oauth2",
        "description": "Access OneDrive, SharePoint, and Microsoft Graph",
        "icon": "microsoft",
        "actions": ["list_files", "read_file", "list_sites", "list_users", "send_email"],
        "events": ["file_modified", "message_received"],
    },
    {
        "name": "Dropbox",
        "connector_type": "dropbox",
        "category": "storage",
        "auth_type": "oauth2",
        "description": "Manage Dropbox files and folders",
        "icon": "dropbox",
        "actions": ["list_files", "read_file", "upload_file", "search", "get_file_link"],
        "events": ["file_added", "file_deleted"],
    },
    {
        "name": "Stripe",
        "connector_type": "stripe",
        "category": "finance",
        "auth_type": "api_key",
        "description": "View payments, customers, subscriptions, and invoices",
        "icon": "stripe",
        "actions": ["list_payments", "list_customers", "list_subscriptions", "list_invoices", "get_balance"],
        "events": ["payment_succeeded", "payment_failed", "invoice_paid", "subscription_updated"],
    },
    {
        "name": "Notion",
        "connector_type": "notion",
        "category": "productivity",
        "auth_type": "oauth2",
        "description": "Read and write Notion pages, databases, and blocks",
        "icon": "notion",
        "actions": ["list_databases", "query_database", "get_page", "create_page", "append_blocks"],
        "events": ["page_updated", "database_updated"],
    },
    {
        "name": "Discord",
        "connector_type": "discord",
        "category": "communication",
        "auth_type": "oauth2",
        "description": "Send messages, manage channels, and moderate servers",
        "icon": "discord",
        "actions": ["send_message", "list_channels", "get_channel_history", "list_members"],
        "events": ["message_sent", "member_joined"],
    },
    {
        "name": "Telegram",
        "connector_type": "telegram",
        "category": "communication",
        "auth_type": "bot_token",
        "description": "Send messages, manage bots, and receive updates",
        "icon": "telegram",
        "actions": ["send_message", "send_photo", "get_updates", "list_chats"],
        "events": ["message_received", "callback_query"],
    },
    {
        "name": "WhatsApp Business",
        "connector_type": "whatsapp_business",
        "category": "communication",
        "auth_type": "api_key",
        "description": "Send and receive WhatsApp Business messages",
        "icon": "whatsapp",
        "actions": ["send_message", "send_template", "get_templates", "list_phone_numbers"],
        "events": ["incoming_message", "message_status"],
    },
    {
        "name": "HubSpot CRM",
        "connector_type": "hubspot",
        "category": "crm",
        "auth_type": "oauth2",
        "description": "Manage contacts, deals, tickets, and companies",
        "icon": "hubspot",
        "actions": ["list_contacts", "create_contact", "list_deals", "list_companies", "list_tickets"],
        "events": ["contact_created", "deal_stage_changed"],
    },
    {
        "name": "Jira",
        "connector_type": "jira",
        "category": "project_management",
        "auth_type": "api_key",
        "description": "Manage issues, projects, and sprints in Jira",
        "icon": "jira",
        "actions": ["list_projects", "list_issues", "create_issue", "search_issues", "get_issue"],
        "events": ["issue_created", "issue_updated"],
    },
    {
        "name": "Linear",
        "connector_type": "linear",
        "category": "project_management",
        "auth_type": "api_key",
        "description": "Manage issues, projects, and teams in Linear",
        "icon": "linear",
        "actions": ["list_teams", "list_issues", "create_issue", "search_issues", "list_projects"],
        "events": ["issue_created", "issue_updated"],
    },
]


class ConnectorManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_definitions(self) -> int:
        count = 0
        for def_data in CONNECTOR_DEFINITIONS:
            existing = await self.db.execute(
                select(ConnectorDefinition).where(ConnectorDefinition.connector_type == def_data["connector_type"])
            )
            if existing.scalar_one_or_none():
                continue
            definition = ConnectorDefinition(
                **{k: v for k, v in def_data.items() if k != "icon"},
                icon_url=def_data.get("icon"),
                config_schema=def_data.get("config_schema", {}),
                permissions=def_data.get("permissions", []),
            )
            self.db.add(definition)
            count += 1
        if count:
            await self.db.commit()
        return count

    async def list_definitions(self, category: str | None = None, connector_type: str | None = None) -> list[ConnectorDefinition]:
        q = select(ConnectorDefinition).where(ConnectorDefinition.is_active == True)
        if category:
            q = q.where(ConnectorDefinition.category == category)
        if connector_type:
            q = q.where(ConnectorDefinition.connector_type == connector_type)
        q = q.order_by(ConnectorDefinition.name)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def install_connector(self, org_id: uuid.UUID, connector_id: uuid.UUID, name: str, config: dict | None, created_by: uuid.UUID) -> ConnectorIntegration:
        integ = ConnectorIntegration(
            organization_id=org_id, connector_id=connector_id,
            name=name, status="disconnected", config=config or {},
            settings={}, is_active=True,
            created_by=created_by,
        )
        self.db.add(integ)
        await self.db.commit()
        await self.db.refresh(integ)
        log = ConnectorLog(
            integration_id=integ.id, organization_id=org_id,
            level="info", action="install", message=f"Connector '{name}' installed",
        )
        self.db.add(log)
        await self.db.commit()
        return integ

    async def list_integrations(self, org_id: uuid.UUID) -> list[ConnectorIntegration]:
        rows = await self.db.execute(
            select(ConnectorIntegration).where(ConnectorIntegration.organization_id == org_id).order_by(ConnectorIntegration.created_at.desc())
        )
        return list(rows.scalars().all())

    async def get_integration(self, integration_id: uuid.UUID) -> ConnectorIntegration | None:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        return rows.scalar_one_or_none()

    async def uninstall_connector(self, integration_id: uuid.UUID) -> bool:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return False
        await self.db.delete(integ)
        await self.db.commit()
        return True

    async def get_dashboard(self, org_id: uuid.UUID) -> dict:
        total_q = await self.db.execute(
            select(func.count(ConnectorIntegration.id)).where(ConnectorIntegration.organization_id == org_id)
        )
        total = total_q.scalar() or 0
        active_q = await self.db.execute(
            select(func.count(ConnectorIntegration.id)).where(
                ConnectorIntegration.organization_id == org_id,
                ConnectorIntegration.status == "connected",
                ConnectorIntegration.is_active == True,
            )
        )
        active = active_q.scalar() or 0
        from app.models.v5_connector_platform import SyncJob, WebhookEvent
        syncs_q = await self.db.execute(
            select(func.count(SyncJob.id)).where(SyncJob.organization_id == org_id)
        )
        syncs = syncs_q.scalar() or 0
        wh_q = await self.db.execute(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.organization_id == org_id)
        )
        webhooks = wh_q.scalar() or 0
        last_sync_q = await self.db.execute(
            select(func.max(SyncJob.started_at)).where(SyncJob.organization_id == org_id)
        )
        last_sync_at = last_sync_q.scalar()
        recent_wh_q = await self.db.execute(
            select(func.count(WebhookEvent.id)).where(
                WebhookEvent.organization_id == org_id,
                WebhookEvent.created_at >= datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
        recent_webhooks = recent_wh_q.scalar() or 0
        cats_q = await self.db.execute(
            select(ConnectorDefinition.category, func.count(ConnectorIntegration.id)).join(
                ConnectorIntegration, ConnectorDefinition.id == ConnectorIntegration.connector_id
            ).where(ConnectorIntegration.organization_id == org_id).group_by(ConnectorDefinition.category)
        )
        by_category = {row[0]: row[1] for row in cats_q.all()}
        logs_q = await self.db.execute(
            select(func.count(ConnectorLog.id)).where(
                ConnectorLog.organization_id == org_id, ConnectorLog.level == "error"
            )
        )
        errors = logs_q.scalar() or 0
        return {
            "total_connectors": total,
            "active_connectors": active,
            "total_syncs": syncs,
            "last_sync_at": last_sync_at,
            "total_webhooks": webhooks,
            "recent_webhooks": recent_webhooks,
            "total_errors": errors,
            "by_category": by_category,
        }

    async def execute_connector_action(self, integration_id: uuid.UUID, action: str, params: dict | None) -> dict:
        from app.services.connector_platform.authentication_service import AuthenticationService
        auth_service = AuthenticationService(self.db)

        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        token = await auth_service.get_active_token(integration_id)
        if not token:
            return {"error": "No active credentials. Please authenticate first."}

        def_rows = await self.db.execute(select(ConnectorDefinition).where(ConnectorDefinition.id == integ.connector_id))
        definition = def_rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector definition not found"}

        result = await self._call_external_api(definition.connector_type, action, params or {}, token)
        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="info" if "error" not in result else "error",
            action=action, message=f"Action '{action}' executed",
            details={"params": params, "result_status": "success" if "error" not in result else "failed"},
        )
        self.db.add(log)
        await self.db.commit()
        return result

    async def _call_external_api(self, connector_type: str, action: str, params: dict, token: str) -> dict:
        handler_map = {
            "google_drive": self._call_google_drive,
            "gmail": self._call_gmail,
            "github": self._call_github,
            "slack": self._call_slack,
            "microsoft_365": self._call_microsoft_graph,
            "dropbox": self._call_dropbox,
            "stripe": self._call_stripe,
        }
        handler = handler_map.get(connector_type)
        if handler:
            try:
                return await handler(action, params, token)
            except Exception as e:
                logger.error("Connector API call failed", extra={"connector": connector_type, "action": action, "error": str(e)})
                return {"error": str(e)}
        return {"error": f"Connector type '{connector_type}' not yet implemented as a real integration"}

    async def _call_google_drive(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_files":
                page_size = params.get("page_size", 20)
                query = params.get("query", "")
                q = f"q={query}&pageSize={page_size}" if query else f"pageSize={page_size}"
                r = await client.get(f"https://www.googleapis.com/drive/v3/files?{q}", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"files": [{"id": f["id"], "name": f["name"], "mime_type": f.get("mimeType"), "size": f.get("size")} for f in data.get("files", [])]}
            if action == "read_file":
                file_id = params.get("file_id", "")
                r = await client.get(f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media", headers=headers)
                r.raise_for_status()
                return {"content": r.text, "file_id": file_id}
            if action == "search":
                query = params.get("query", "")
                r = await client.get(f"https://www.googleapis.com/drive/v3/files?q=name contains '{query}'", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"files": data.get("files", [])}
        return {"error": f"Unsupported action: {action}"}

    async def _call_gmail(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_emails":
                max_results = params.get("max_results", 10)
                query = params.get("query", "")
                q = f"?maxResults={max_results}" + (f"&q={query}" if query else "")
                r = await client.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages{q}", headers=headers)
                r.raise_for_status()
                messages = r.json().get("messages", [])
                full_messages = []
                for m in messages[:5]:
                    mr = await client.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}", headers=headers)
                    if mr.is_success:
                        md = mr.json()
                        headers_dict = {h["name"]: h["value"] for h in md.get("payload", {}).get("headers", [])}
                        full_messages.append({
                            "id": md["id"],
                            "subject": headers_dict.get("Subject", ""),
                            "from": headers_dict.get("From", ""),
                            "date": headers_dict.get("Date", ""),
                            "snippet": md.get("snippet", ""),
                        })
                return {"messages": full_messages}
            if action == "send_email":
                import base64
                to = params.get("to", "")
                subject = params.get("subject", "")
                body = params.get("body", "")
                email_content = f"From: me\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
                encoded = base64.urlsafe_b64encode(email_content.encode()).decode()
                r = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"raw": encoded},
                )
                r.raise_for_status()
                return {"status": "sent", "message_id": r.json().get("id")}
        return {"error": f"Unsupported action: {action}"}

    async def _call_github(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_repos":
                r = await client.get("https://api.github.com/user/repos?per_page=100", headers=headers)
                r.raise_for_status()
                return {"repositories": [{"id": r["id"], "name": r["full_name"], "url": r["html_url"], "description": r.get("description"), "language": r.get("language")} for r in r.json()]}
            if action == "create_issue":
                repo = params.get("repo", "")
                title = params.get("title", "")
                body_text = params.get("body", "")
                r = await client.post(
                    f"https://api.github.com/repos/{repo}/issues",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"title": title, "body": body_text},
                )
                r.raise_for_status()
                d = r.json()
                return {"issue": {"id": d["id"], "number": d["number"], "title": d["title"], "url": d["html_url"], "state": d["state"]}}
            if action == "list_issues":
                repo = params.get("repo", "")
                state = params.get("state", "open")
                r = await client.get(f"https://api.github.com/repos/{repo}/issues?state={state}&per_page=50", headers=headers)
                r.raise_for_status()
                return {"issues": [{"id": i["id"], "number": i["number"], "title": i["title"], "state": i["state"], "user": i["user"]["login"]} for i in r.json()]}
            if action == "search_code":
                query = params.get("query", "")
                r = await client.get(f"https://api.github.com/search/code?q={query}&per_page=10", headers=headers)
                r.raise_for_status()
                d = r.json()
                return {"total_count": d.get("total_count", 0), "items": [{"name": i["name"], "path": i["path"], "repository": i["repository"]["full_name"]} for i in d.get("items", [])]}
            if action == "get_readme":
                repo = params.get("repo", "")
                r = await client.get(f"https://api.github.com/repos/{repo}/readme", headers={**headers, "Accept": "application/vnd.github.raw+json"})
                r.raise_for_status()
                return {"content": r.text, "repo": repo}
        return {"error": f"Unsupported action: {action}"}

    async def _call_slack(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "send_message":
                r = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=headers, json={"channel": params.get("channel", ""), "text": params.get("message", "")},
                )
                r.raise_for_status()
                d = r.json()
                if not d.get("ok"):
                    return {"error": d.get("error", "Slack API error")}
                return {"status": "sent", "channel": params.get("channel"), "ts": d.get("ts")}
            if action == "list_channels":
                r = await client.get("https://slack.com/api/conversations.list?types=public_channel,private_channel&limit=100", headers=headers)
                r.raise_for_status()
                d = r.json()
                return {"channels": [{"id": c["id"], "name": c["name"], "member_count": c.get("num_members")} for c in d.get("channels", [])]}
            if action == "get_channel_history":
                r = await client.get(f"https://slack.com/api/conversations.history?channel={params.get('channel', '')}&limit={params.get('limit', 20)}", headers=headers)
                r.raise_for_status()
                d = r.json()
                return {"messages": [{"ts": m["ts"], "user": m.get("user", ""), "text": m.get("text", "")} for m in d.get("messages", [])]}
        return {"error": f"Unsupported action: {action}"}

    async def _call_microsoft_graph(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_files":
                r = await client.get("https://graph.microsoft.com/v1.0/me/drive/root/children", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"files": [{"id": f["id"], "name": f["name"], "size": f.get("size"), "folder": "folder" in f} for f in data.get("value", [])]}
            if action == "list_users":
                r = await client.get("https://graph.microsoft.com/v1.0/users?$top=50", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"users": [{"id": u["id"], "display_name": u.get("displayName"), "email": u.get("mail", u.get("userPrincipalName"))} for u in data.get("value", [])]}
        return {"error": f"Unsupported action: {action}"}

    async def _call_dropbox(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_files":
                r = await client.post("https://api.dropboxapi.com/2/files/list_folder", headers=headers, json={"path": params.get("path", ""), "limit": params.get("limit", 50)})
                r.raise_for_status()
                data = r.json()
                return {"files": [{"id": e["id"], "name": e["name"], "type": "folder" if ".tag" in e and e[".tag"] == "folder" else "file", "size": e.get("size")} for e in data.get("entries", [])]}
            if action == "read_file":
                path = params.get("path", "")
                r = await client.post("https://content.dropboxapi.com/2/files/download", headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path})})
                r.raise_for_status()
                return {"content": r.text, "path": path}
        return {"error": f"Unsupported action: {action}"}

    async def _call_stripe(self, action: str, params: dict, token: str) -> dict:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}
        base = "https://api.stripe.com/v1"
        async with httpx.AsyncClient(timeout=30.0) as client:
            if action == "list_payments":
                limit = params.get("limit", 10)
                r = await client.get(f"{base}/charges?limit={limit}", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"payments": [{"id": c["id"], "amount": c["amount"], "currency": c["currency"], "status": c["status"], "created": c["created"]} for c in data.get("data", [])]}
            if action == "get_balance":
                r = await client.get(f"{base}/balance", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"available": [{"amount": b["amount"], "currency": b["currency"]} for b in data.get("available", [])], "pending": [{"amount": b["amount"], "currency": b["currency"]} for b in data.get("pending", [])]}
        return {"error": f"Unsupported action: {action}"}

    async def query_connector(self, integration_id: uuid.UUID, action: str, params: dict | None) -> dict:
        return await self.execute_connector_action(integration_id, action, params)
