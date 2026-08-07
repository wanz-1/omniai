from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v3_collaboration import (
    AICommunication,
    AIMeetingSession,
    DeviceTelemetry,
    LearningPath,
    PhysicalDevice,
)
from app.services.ai_service import ai_service


class CollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_meeting(self, title, transcript, participants=None):
        prompt = f"""Analyze this meeting transcript and provide:
1. Executive summary
2. Key decisions made
3. Action items with assignees
4. Key topics discussed

Meeting Title: {title}
Participants: {participants or 'Unknown'}
Transcript:
{transcript}"""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
        return {
            "summary": result.get("content", ""),
            "decisions": [], "action_items": [], "key_topics": [],
        }

    async def save_meeting(self, user_id, title, transcript=None, participants=None, summary=None, decisions=None, action_items=None):
        meeting = AIMeetingSession(
            user_id=user_id, title=title, transcript=transcript,
            participants=participants or [], summary=summary,
            decisions=decisions or [], action_items=action_items or [],
            status="completed" if transcript else "scheduled",
        )
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    async def list_meetings(self, user_id):
        rows = await self.db.execute(
            select(AIMeetingSession).where(AIMeetingSession.user_id == user_id).order_by(AIMeetingSession.created_at.desc())
        )
        return list(rows.scalars().all())

    async def generate_communication(self, user_id, comm_type, title, content=None, recipient=None, tone="professional"):
        prompt = f"""Generate a {comm_type} with the following details:
Title: {title}
Content to address: {content or 'N/A'}
Recipient: {recipient or 'General'}
Tone: {tone}

Create a well-written, professional communication."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1024)
        comm = AICommunication(
            user_id=user_id, communication_type=comm_type, title=title,
            content=content, recipient=recipient, tone=tone,
            generated_content=result.get("content", ""), status="generated",
        )
        self.db.add(comm)
        await self.db.commit()
        await self.db.refresh(comm)
        return comm

    async def list_communications(self, user_id, comm_type=None):
        query = select(AICommunication).where(AICommunication.user_id == user_id)
        if comm_type:
            query = query.where(AICommunication.communication_type == comm_type)
        query = query.order_by(AICommunication.created_at.desc())
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def create_learning_path(self, user_id, title, subject, skill_level="beginner", goals=None, description=None):
        prompt = f"""Create a personalized learning path for:
Subject: {subject}
Current Level: {skill_level}
Goals: {goals or 'General knowledge'}
Description: {description or title}

Provide a structured curriculum with modules, estimated hours per module, and learning resources."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=2048)
        path = LearningPath(
            user_id=user_id, title=title, description=description,
            subject=subject, skill_level=skill_level, goals=goals or [],
            modules=[{"generated": True}], status="active",
        )
        self.db.add(path)
        await self.db.commit()
        await self.db.refresh(path)
        return path, result.get("content", "")

    async def list_learning_paths(self, user_id):
        rows = await self.db.execute(
            select(LearningPath).where(LearningPath.user_id == user_id).order_by(LearningPath.created_at.desc())
        )
        return list(rows.scalars().all())

    async def register_device(self, user_id, name, device_type, protocol="mqtt", endpoint=None, capabilities=None, organization_id=None):
        device = PhysicalDevice(
            user_id=user_id, organization_id=organization_id, name=name,
            device_type=device_type, protocol=protocol, endpoint=endpoint,
            capabilities=capabilities or [],
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def list_devices(self, user_id, device_type=None):
        query = select(PhysicalDevice).where(PhysicalDevice.user_id == user_id)
        if device_type:
            query = query.where(PhysicalDevice.device_type == device_type)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def record_telemetry(self, device_id, metric_name, metric_value, unit=None):
        telemetry = DeviceTelemetry(
            device_id=device_id, metric_name=metric_name,
            metric_value=metric_value, unit=unit,
            recorded_at=datetime.now(UTC),
        )
        self.db.add(telemetry)
        await self.db.commit()
        await self.db.refresh(telemetry)
        device = await self.db.get(PhysicalDevice, device_id)
        if device:
            device.last_seen = datetime.now(UTC)
            device.status = "online"
            await self.db.commit()
        return telemetry
