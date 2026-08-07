from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v3_personal import (
    ExecutiveAssistant,
    PersonalAIAssistant,
    PersonalMemory,
    PersonalTask,
)
from app.services.ai_service import ai_service

EXECUTIVE_PROMPTS = {
    "ceo": "You are an AI CEO Assistant. Provide strategic business advice, growth recommendations, performance analysis, and high-level planning support.",
    "cfo": "You are an AI CFO Assistant. Provide financial planning, forecasting, risk analysis, investment advice, and budget optimization.",
    "cto": "You are an AI CTO Assistant. Provide technology strategy, system architecture guidance, security planning, and technical decision support.",
    "coo": "You are an AI COO Assistant. Provide operations management, workflow optimization, process improvement, and operational efficiency analysis.",
}


class PersonalAIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assistant(self, user_id, name, role, personality=None, capabilities=None):
        prompts = {
            "chief": "You are a personal AI chief assistant. Manage tasks, prepare reports, organize information, schedule activities, research topics, draft communications, and monitor priorities.",
            "executive": "You are a high-level executive assistant focused on strategic support, decision-making, and leadership coordination.",
            "personal": "You are a personal AI companion focused on individual productivity, learning, and daily task management.",
        }
        assistant = PersonalAIAssistant(
            user_id=user_id, name=name, role=role,
            personality=personality or "professional",
            system_prompt=prompts.get(role, prompts["personal"]),
            capabilities=capabilities or ["task_management", "information_organization", "communication"],
        )
        self.db.add(assistant)
        await self.db.commit()
        await self.db.refresh(assistant)
        return assistant

    async def list_assistants(self, user_id):
        rows = await self.db.execute(
            select(PersonalAIAssistant).where(PersonalAIAssistant.user_id == user_id).order_by(PersonalAIAssistant.created_at.desc())
        )
        return list(rows.scalars().all())

    async def query_assistant(self, assistant_id, query_text, context=None):
        assistant = await self.db.get(PersonalAIAssistant, assistant_id)
        if not assistant:
            return {"response": "Assistant not found"}
        memories = (await self.db.execute(
            select(PersonalMemory).where(PersonalMemory.assistant_id == assistant_id).order_by(PersonalMemory.importance.desc()).limit(10)
        )).scalars().all()
        tasks = (await self.db.execute(
            select(PersonalTask).where(PersonalTask.assistant_id == assistant_id).where(PersonalTask.status == "pending").limit(10)
        )).scalars().all()
        ctx = context or {}
        memory_context = "\n".join([f"- {m.title}: {m.summary or m.content[:200]}" for m in memories if m.content]) if memories else "No memories yet."
        task_context = "\n".join([f"- {t.title} ({t.priority})" for t in tasks]) if tasks else "No pending tasks."
        system = assistant.system_prompt or "You are a helpful personal AI assistant."
        prompt = f"""Context:
{chr(10).join([f"{k}: {v}" for k, v in ctx.items()])}

Relevant Memories:
{memory_context}

Current Tasks:
{task_context}

User Query: {query_text}"""
        result = await ai_service.complete([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=2048)

        assistant.total_interactions += 1
        await self.db.commit()
        return {"response": result.get("content", ""), "sources": [{"title": m.title, "type": m.memory_type} for m in memories]}

    async def create_task(self, assistant_id, user_id, title, description=None, priority="medium", category=None, due_date=None):
        task = PersonalTask(
            assistant_id=assistant_id, user_id=user_id, title=title,
            description=description, priority=priority, category=category,
            due_date=due_date, status="pending",
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def list_tasks(self, user_id, status=None):
        query = select(PersonalTask).where(PersonalTask.user_id == user_id)
        if status:
            query = query.where(PersonalTask.status == status)
        query = query.order_by(PersonalTask.created_at.desc())
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def complete_task(self, task_id, result_text=None):
        task = await self.db.get(PersonalTask, task_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = result_text and None
        if result_text:
            task.result = result_text
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def store_memory(self, assistant_id, user_id, memory_type, title, content=None, summary=None, importance=0, tags=None):
        memory = PersonalMemory(
            assistant_id=assistant_id, user_id=user_id, memory_type=memory_type,
            title=title, content=content, summary=summary,
            importance=importance, tags=tags or [],
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def search_memories(self, user_id, query_text=None):
        rows = await self.db.execute(
            select(PersonalMemory).where(PersonalMemory.user_id == user_id).order_by(PersonalMemory.importance.desc()).limit(20)
        )
        return list(rows.scalars().all())

    async def create_executive(self, user_id, role, name, description=None, organization_id=None):
        prompt = EXECUTIVE_PROMPTS.get(role, "You are an AI executive assistant.")
        caps = {
            "ceo": ["strategic_planning", "business_analysis", "growth_recommendations", "performance_reviews"],
            "cfo": ["financial_planning", "forecasting", "risk_analysis", "investment_analysis"],
            "cto": ["technology_decisions", "system_architecture", "security_planning", "technical_strategy"],
            "coo": ["operations", "workflow_optimization", "process_improvement", "efficiency_analysis"],
        }
        exec_asst = ExecutiveAssistant(
            user_id=user_id, organization_id=organization_id, role=role,
            name=name, description=description, system_prompt=prompt,
            capabilities=caps.get(role, ["general"]),
        )
        self.db.add(exec_asst)
        await self.db.commit()
        await self.db.refresh(exec_asst)
        return exec_asst

    async def list_executives(self, user_id):
        rows = await self.db.execute(
            select(ExecutiveAssistant).where(ExecutiveAssistant.user_id == user_id)
        )
        return list(rows.scalars().all())

    async def query_executive(self, exec_id, query_text):
        exec_asst = await self.db.get(ExecutiveAssistant, exec_id)
        if not exec_asst:
            return {"response": "Executive assistant not found"}
        prompt = f"As {exec_asst.role.upper()} assistant: {query_text}"
        result = await ai_service.complete([
            {"role": "system", "content": exec_asst.system_prompt or "You are an AI executive."},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=2048)
        return {"response": result.get("content", ""), "role": exec_asst.role}
