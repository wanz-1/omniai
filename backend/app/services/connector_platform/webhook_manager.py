import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ssrf import SSRFBlockedError, validate_outbound_url
from app.models.v5_connector_platform import ConnectorIntegration, ConnectorLog, WebhookEvent

logger = logging.getLogger("omniai.connector.webhook")

MAX_RETRIES = 3
RETRY_DELAYS = [5, 30, 120]


def _compute_signature(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class WebhookManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_webhook(self, integration_id: uuid.UUID, event_type: str, target_url: str, secret: str | None = None) -> dict:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        config = dict(integ.config or {})
        webhooks = config.get("webhooks", [])
        webhook_entry = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "target_url": target_url,
            "secret": secret or "",
            "registered_at": datetime.now(UTC).isoformat(),
        }
        webhooks.append(webhook_entry)
        config["webhooks"] = webhooks
        integ.config = config
        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="info", action="webhook_register", message=f"Webhook registered for {event_type}",
        )
        self.db.add(log)
        await self.db.commit()
        return {"status": "registered", "event_type": event_type, "target_url": target_url, "webhook_id": webhook_entry["id"]}

    async def receive_event(self, org_id: uuid.UUID, integration_id: uuid.UUID | None, source: str, event_type: str, payload: dict) -> WebhookEvent:
        event = WebhookEvent(
            organization_id=org_id, integration_id=integration_id,
            source=source, event_type=event_type, payload=payload,
            status="received",
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def deliver_webhook(self, event_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(WebhookEvent).where(WebhookEvent.id == event_id))
        event = rows.scalar_one_or_none()
        if not event:
            return {"error": "Event not found"}

        if not event.integration_id:
            event.status = "failed"
            event.error_log = [{"message": "No integration associated with this event"}]
            await self.db.commit()
            return {"error": "No integration associated"}

        integ_rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == event.integration_id))
        integ = integ_rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        webhooks = (integ.config or {}).get("webhooks", [])
        delivery_results = []
        for wh in webhooks:
            if wh.get("event_type") != event.event_type:
                continue
            target_url = wh.get("target_url", "")
            secret = wh.get("secret", "")
            result = await self._deliver_to_url(target_url, secret, event, integ)
            delivery_results.append(result)

        if not delivery_results:
            event.status = "processed"
            event.processed_at = datetime.now(UTC)
        await self.db.commit()
        return {
            "event_id": str(event_id),
            "delivery_results": delivery_results,
            "status": event.status,
        }

    async def _deliver_to_url(self, target_url: str, secret: str, event: WebhookEvent, integ: ConnectorIntegration) -> dict:
        try:
            await validate_outbound_url(target_url)
        except SSRFBlockedError as e:
            log = ConnectorLog(
                integration_id=integ.id, organization_id=integ.organization_id,
                level="error", action="webhook_blocked",
                message=f"Webhook delivery blocked: {e}",
            )
            self.db.add(log)
            return {"target_url": target_url, "status": "blocked", "reason": str(e), "attempts": 0}

        payload_body = json.dumps({
            "event_id": str(event.id),
            "event_type": event.event_type,
            "source": event.source,
            "payload": event.payload,
            "timestamp": event.created_at.isoformat() if event.created_at else datetime.now(UTC).isoformat(),
        }).encode()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OmniAI-Webhook/1.0",
        }
        if secret:
            signature = _compute_signature(payload_body, secret)
            headers["X-OmniAI-Signature"] = signature
            headers["X-OmniAI-Timestamp"] = str(int(datetime.now(UTC).timestamp()))

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(target_url, content=payload_body, headers=headers)
                    response.raise_for_status()
                    log = ConnectorLog(
                        integration_id=integ.id, organization_id=integ.organization_id,
                        level="info", action="webhook_delivery",
                        message=f"Webhook delivered to {target_url} (attempt {attempt + 1})",
                    )
                    self.db.add(log)
                    return {
                        "target_url": target_url,
                        "status": "delivered",
                        "status_code": response.status_code,
                        "attempts": attempt + 1,
                    }
            except httpx.TimeoutException as e:
                last_error = str(e)
                logger.warning("Webhook delivery timeout", extra={"url": target_url, "attempt": attempt + 1})
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(RETRY_DELAYS[attempt])
            except httpx.HTTPStatusError as e:
                last_error = str(e)
                logger.warning("Webhook delivery HTTP error", extra={"url": target_url, "status": e.response.status_code, "attempt": attempt + 1})
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(RETRY_DELAYS[attempt])
            except Exception as e:
                last_error = str(e)
                logger.error("Webhook delivery failed", extra={"url": target_url, "error": str(e)})
                break

        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="error", action="webhook_failed",
            message=f"Webhook delivery failed to {target_url}: {last_error}",
        )
        self.db.add(log)
        event.status = "failed"
        errors = event.error_log or []
        errors.append({"message": f"Delivery failed to {target_url}: {last_error}", "attempts": MAX_RETRIES})
        event.error_log = errors
        return {
            "target_url": target_url,
            "status": "failed",
            "error": last_error,
        }

    async def process_event(self, event_id: uuid.UUID) -> dict:
        delivery_result = await self.deliver_webhook(event_id)
        return delivery_result

    async def list_events(self, org_id: uuid.UUID, status: str | None = None, limit: int = 50) -> list[WebhookEvent]:
        q = select(WebhookEvent).where(WebhookEvent.organization_id == org_id)
        if status:
            q = q.where(WebhookEvent.status == status)
        q = q.order_by(WebhookEvent.created_at.desc()).limit(limit)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def get_webhook_summary(self, org_id: uuid.UUID) -> dict:
        total_q = await self.db.execute(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.organization_id == org_id)
        )
        total = total_q.scalar() or 0
        pending_q = await self.db.execute(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.organization_id == org_id, WebhookEvent.status == "received")
        )
        pending = pending_q.scalar() or 0
        failed_q = await self.db.execute(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.organization_id == org_id, WebhookEvent.status == "failed")
        )
        failed = failed_q.scalar() or 0
        return {"total_events": total, "pending": pending, "failed": failed}
