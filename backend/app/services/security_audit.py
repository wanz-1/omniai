import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEventV6

SecurityEvent = SecurityEventV6

logger = logging.getLogger("omniai.security_audit")


class SecurityAuditService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    async def log_event(
        self,
        event_type: str,
        action: str,
        user_id: str = "",
        organization_id: str = "",
        severity: str = "info",
        ip_address: str = "",
        user_agent: str = "",
        resource_type: str = "",
        resource_id: str = "",
        result: str = "success",
        detail: str = "",
        extra: dict[str, Any] | None = None,
    ) -> SecurityEventV6:
        event = SecurityEventV6(
            id=uuid.uuid4(),
            user_id=user_id or None,
            organization_id=organization_id or None,
            event_type=event_type,
            severity=severity,
            ip_address=ip_address or None,
            user_agent=user_agent or None,
            action=action,
            resource_type=resource_type or None,
            resource_id=resource_id or None,
            result=result,
            detail=detail or None,
            meta_data=extra,
            event_timestamp=datetime.now(UTC),
        )

        if self.db:
            self.db.add(event)
            await self.db.flush()

        log_level = logging.WARNING if severity in ("high", "critical") else logging.INFO
        logger.log(
            log_level,
            "Security event: %s - %s (%s)",
            event_type,
            action,
            result,
            extra={
                "event": "security_audit",
                "security_event_type": event_type,
                "security_severity": severity,
                "security_action": action,
                "security_result": result,
                "user_id": user_id,
                "organization_id": organization_id,
            },
        )

        return event

    async def log_login_attempt(
        self,
        user_id: str,
        success: bool,
        ip_address: str = "",
        user_agent: str = "",
        detail: str = "",
    ) -> SecurityEvent:
        return await self.log_event(
            event_type="login_attempt",
            action="user.login",
            user_id=user_id,
            severity="warning" if not success else "info",
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="auth",
            result="success" if success else "failure",
            detail=detail or ("Login successful" if success else "Login failed"),
        )

    async def log_permission_change(
        self,
        actor_id: str,
        target_user_id: str,
        organization_id: str,
        old_role: str,
        new_role: str,
    ) -> SecurityEvent:
        return await self.log_event(
            event_type="permission_change",
            action="user.role_changed",
            user_id=actor_id,
            organization_id=organization_id,
            severity="high",
            resource_type="permission",
            resource_id=target_user_id,
            detail=f"Role changed from {old_role} to {new_role}",
        )

    async def log_ai_guard_block(
        self,
        user_id: str,
        guard_type: str,
        risk_level: str,
        flags: list[str],
        content_preview: str = "",
    ) -> SecurityEvent:
        return await self.log_event(
            event_type="ai_guard_block",
            action=f"ai_security.{guard_type}",
            user_id=user_id,
            severity="high",
            resource_type="ai_security",
            result="blocked",
            detail=f"AI {guard_type} blocked at {risk_level} risk",
            extra={"flags": flags, "content_preview": content_preview[:500]},
        )

    async def log_api_key_usage(
        self,
        user_id: str,
        api_key_id: str,
        ip_address: str,
        endpoint: str,
        success: bool,
    ) -> SecurityEvent:
        return await self.log_event(
            event_type="api_key_usage",
            action="api_key.access",
            user_id=user_id,
            severity="info",
            ip_address=ip_address,
            resource_type="api_key",
            resource_id=api_key_id,
            result="success" if success else "failure",
            detail=f"API key used for {endpoint}",
        )

    async def log_data_export(
        self,
        user_id: str,
        organization_id: str,
        export_type: str,
        record_count: int,
    ) -> SecurityEvent:
        return await self.log_event(
            event_type="data_export",
            action="data.export",
            user_id=user_id,
            organization_id=organization_id,
            severity="medium",
            resource_type="data",
            detail=f"Exported {record_count} {export_type} records",
            extra={"export_type": export_type, "record_count": record_count},
        )

    async def get_recent_events(
        self,
        db: AsyncSession,
        limit: int = 50,
        event_type: str | None = None,
        severity: str | None = None,
        user_id: str | None = None,
    ) -> list[SecurityEvent]:
        query = select(SecurityEvent).order_by(SecurityEvent.event_timestamp.desc())

        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)
        if severity:
            query = query.where(SecurityEvent.severity == severity)
        if user_id:
            query = query.where(SecurityEvent.user_id == user_id)

        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


security_audit = SecurityAuditService()
