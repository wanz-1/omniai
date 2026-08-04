import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_network import AutonomousResearch
from app.services.ai_service import ai_service


RESEARCH_SYSTEM_PROMPT = """You are an autonomous research AI. Your process:
1. Analyze the research topic and determine key questions
2. Search for relevant information and sources
3. Analyze and cross-reference findings
4. Synthesize a comprehensive report
5. Provide actionable recommendations

For each source you reference, provide: title, url (if applicable), and relevance.
Structure your output with: summary, key findings, analysis, and recommendations."""


class AutonomousResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def conduct_research(
        self,
        title: str,
        topic: str,
        depth: str = "standard",
        user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        context: str | None = None,
    ) -> AutonomousResearch:
        research = AutonomousResearch(
            title=title,
            topic=topic,
            depth=depth,
            status="in_progress",
            user_id=user_id,
            organization_id=organization_id,
        )
        self.db.add(research)
        await self.db.flush()

        try:
            search_queries = await self._generate_queries(topic, depth)
            research.search_queries = search_queries

            findings = await self._analyze_topic(topic, depth, context)
            research.findings = findings.get("findings", {})
            research.summary = findings.get("summary", "")
            research.sources = findings.get("sources", [])
            research.confidence = findings.get("confidence", 0.7)

            report = await self._generate_report(title, topic, findings)
            research.report = report
            research.recommendations = findings.get("recommendations", [])

            research.status = "completed"
            research.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            research.status = "failed"
            research.findings = {"error": str(e)}

        await self.db.commit()
        await self.db.refresh(research)
        return research

    async def _generate_queries(self, topic: str, depth: str) -> list[str]:
        max_queries = 5 if depth == "deep" else 3
        messages = [
            {"role": "system", "content": "Generate research search queries as a JSON array of strings."},
            {"role": "user", "content": f"Topic: {topic}\nDepth: {depth}\nGenerate {max_queries} search queries."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.5)
        try:
            queries = json.loads(result["content"])
            return queries[:max_queries] if isinstance(queries, list) else [topic]
        except (json.JSONDecodeError, KeyError):
            return [topic]

    async def _analyze_topic(self, topic: str, depth: str, context: str | None = None) -> dict:
        messages = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Research topic: {topic}\nDepth: {depth}\nContext: {context or 'None'}\n\nProvide comprehensive analysis in JSON format with keys: summary, findings (object), sources (array), recommendations (array), confidence (float 0-1).",
            },
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {
                "summary": result.get("content", "")[:500],
                "findings": {"analysis": result.get("content", "")},
                "sources": [],
                "recommendations": [],
                "confidence": 0.6,
            }

    async def _generate_report(self, title: str, topic: str, findings: dict) -> str:
        messages = [
            {"role": "system", "content": "You are a research report writer. Create a well-structured, professional report."},
            {
                "role": "user",
                "content": f"Title: {title}\nTopic: {topic}\nFindings: {json.dumps(findings, indent=2)}\n\nWrite a comprehensive research report with executive summary, methodology, findings, analysis, and recommendations.",
            },
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        return result.get("content", "")

    async def get_research(self, research_id: uuid.UUID) -> AutonomousResearch | None:
        from sqlalchemy import select
        result = await self.db.execute(select(AutonomousResearch).where(AutonomousResearch.id == research_id))
        return result.scalar_one_or_none()

    async def list_research(self, user_id: uuid.UUID, limit: int = 20) -> list[AutonomousResearch]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(AutonomousResearch)
            .where(AutonomousResearch.user_id == user_id)
            .order_by(AutonomousResearch.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
