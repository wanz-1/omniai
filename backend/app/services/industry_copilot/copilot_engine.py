from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_copilot import CopilotConfig, CopilotSession, CopilotMessage, CopilotDomainRule
from app.services.ai_service import ai_service

class CopilotEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_config(self, organization_id, industry, name=None, created_by=None):
        rows = await self.db.execute(select(CopilotConfig).where(CopilotConfig.organization_id == organization_id, CopilotConfig.industry == industry, CopilotConfig.is_active == True))
        config = rows.scalar_one_or_none()
        if not config:
            config = CopilotConfig(organization_id=organization_id, industry=industry, name=name or f"{industry.title()} Copilot", description=f"AI copilot for {industry}", created_by=created_by or organization_id)
            self.db.add(config); await self.db.commit(); await self.db.refresh(config)
        return config

    async def chat(self, organization_id, user_id, copilot_id, message, session_id=None, context=None):
        if session_id:
            session = await self.db.get(CopilotSession, session_id)
            if not session: session_id = None
        if not session_id:
            session = CopilotSession(organization_id=organization_id, user_id=user_id, copilot_id=copilot_id, title=message[:50])
            self.db.add(session); await self.db.commit(); await self.db.refresh(session)
        dm = CopilotMessage(session_id=session.id, role="user", content=message)
        self.db.add(dm); await self.db.commit()
        config = await self.db.get(CopilotConfig, copilot_id)
        rules = await self.db.execute(select(CopilotDomainRule).where(CopilotDomainRule.organization_id == organization_id, CopilotDomainRule.industry == config.industry if config else None, CopilotDomainRule.is_active == True))
        domain_rules = list(rules.scalars().all())
        rules_text = "\n".join([f"- {r.name}: {r.description}" for r in domain_rules[:5]]) if domain_rules else ""
        prompt = f"""You are {config.name if config else 'an Industry Copilot'}. Industry: {(config.industry if config else 'general').title()}.
Domain rules:{rules_text}
Context: {context or {}}
User: {message}
Provide a helpful, accurate response with actionable recommendations."""
        reply = await ai_service.complete(prompt)
        am = CopilotMessage(session_id=session.id, role="assistant", content=reply)
        self.db.add(am); await self.db.commit()
        return {"session_id": str(session.id), "reply": reply}

    async def execute_workflow(self, workflow_id, input_data):
        from app.models.v5_copilot import CopilotWorkflow, CopilotWorkflowExecution
        from datetime import datetime, timezone
        wf = await self.db.get(CopilotWorkflow, workflow_id)
        if not wf: return None
        exec_record = CopilotWorkflowExecution(workflow_id=workflow_id, organization_id=wf.organization_id, user_id=wf.created_by, status="running", input_data=input_data, started_at=datetime.now(timezone.utc))
        self.db.add(exec_record); await self.db.commit(); await self.db.refresh(exec_record)
        exec_record.status = "completed"; exec_record.output_data = {"result": f"Workflow '{wf.name}' executed with {len(wf.steps)} steps"}
        exec_record.completed_at = datetime.now(timezone.utc)
        await self.db.commit(); await self.db.refresh(exec_record)
        return exec_record
