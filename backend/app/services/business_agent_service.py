import uuid
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.business import (
    ApprovalRequest, BusinessAlert, BusinessMetric, BusinessReport,
    BusinessWorkflow, BusinessWorkflowExecution, FinancialRecord,
    KnowledgeDocument,
)
from app.models.organization import Organization
from app.models.user import User
from app.services.ai_service import ai_service


class BusinessAgentService:
    """Orchestrates all business AI agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_agent_system_prompt(self, agent_type: str) -> str:
        prompts = {
            "business_manager": (
                "You are an AI Business Manager. Analyze business performance, "
                "identify trends, suggest strategic improvements, and generate executive reports. "
                "Be data-driven and provide actionable recommendations."
            ),
            "finance_officer": (
                "You are an AI Finance Officer. Manage budgets, analyze spending, "
                "forecast financial trends, ensure donor compliance, and generate financial reports. "
                "Be precise with numbers and provide clear financial insights."
            ),
            "hr_manager": (
                "You are an AI HR Manager. Screen candidates, create job descriptions, "
                "support employee onboarding, manage leave requests, and provide HR policy guidance. "
                "Be professional and respectful."
            ),
            "operations_manager": (
                "You are an AI Operations Manager. Track projects, monitor workflows, "
                "identify risks, optimize resources, and generate operational reports. "
                "Be systematic and focus on efficiency."
            ),
            "customer_success_manager": (
                "You are an AI Customer Success Manager. Analyze customer feedback, "
                "identify satisfaction trends, suggest improvements, and generate customer insights. "
                "Be empathetic and solution-oriented."
            ),
        }
        return prompts.get(agent_type, "You are a helpful business AI assistant.")

    async def process_query(
        self, agent_type: str, query: str, organization_id: uuid.UUID,
        user_id: uuid.UUID, context: dict | None = None
    ) -> dict:
        metrics = await self._get_recent_metrics(organization_id, agent_type)
        reports = await self._get_recent_reports(organization_id, agent_type)
        knowledge = await self._query_knowledge(organization_id, query)

        system_prompt = self._get_agent_system_prompt(agent_type)
        context_str = f"Organization metrics: {json.dumps(metrics, default=str)[:1000]}\n"
        if reports:
            context_str += f"Recent reports: {json.dumps(reports[:2], default=str)[:1000]}\n"
        if knowledge:
            context_str += f"Knowledge base: {json.dumps(knowledge[:3], default=str)[:1000]}\n"

        response = await ai_service.complete(
            prompt=f"{context_str}\nUser query: {query}",
            system_prompt=system_prompt,
        )
        response_text = response if isinstance(response, str) else response.get("content", response.get("text", ""))

        suggestions = await self._extract_suggestions(response_text)
        if suggestions:
            await self._store_metrics_from_suggestions(organization_id, agent_type, suggestions)

        return {
            "response": response_text,
            "agent_type": agent_type,
            "suggestions": suggestions,
            "context_used": {"metrics_count": len(metrics), "reports_count": len(reports), "knowledge_hits": len(knowledge)},
        }

    async def generate_report(
        self, agent_type: str, report_type: str, organization_id: uuid.UUID,
        user_id: uuid.UUID, period_start: str | None = None,
        period_end: str | None = None
    ) -> BusinessReport:
        metrics = await self._get_recent_metrics(organization_id, agent_type)
        knowledge = await self._query_knowledge(organization_id, f"{report_type} report")

        system_prompt = self._get_agent_system_prompt(agent_type)
        data_str = json.dumps(metrics, default=str)[:3000]

        response = await ai_service.complete(
            prompt=(
                f"Generate a detailed {report_type} report based on this data:\n{data_str}\n\n"
                f"Period: {period_start or 'N/A'} to {period_end or 'N/A'}\n\n"
                "Provide: 1) Executive summary 2) Key findings 3) Detailed analysis "
                "4) Recommendations 5) Data sources used. Format as structured JSON."
            ),
            system_prompt=system_prompt,
        )
        text = response if isinstance(response, str) else response.get("content", response.get("text", ""))

        parsed = await self._parse_report_json(text)
        report = BusinessReport(
            organization_id=organization_id,
            agent_type=agent_type,
            report_type=report_type,
            title=f"{agent_type.replace('_', ' ').title()} — {report_type.replace('_', ' ').title()}",
            content=parsed.get("content", {"raw": text}),
            summary=parsed.get("summary", text[:500]),
            recommendations=parsed.get("recommendations", []),
            data_sources=[{"source": "business_metrics", "count": len(metrics)}],
            period_start=datetime.fromisoformat(period_start) if period_start else None,
            period_end=datetime.fromisoformat(period_end) if period_end else None,
            status="completed",
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def _get_recent_metrics(self, org_id: uuid.UUID, agent_type: str, days: int = 90) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(BusinessMetric).where(
                and_(
                    BusinessMetric.organization_id == org_id,
                    BusinessMetric.agent_type == agent_type,
                    BusinessMetric.created_at >= cutoff,
                )
            ).order_by(BusinessMetric.created_at.desc()).limit(100)
        )
        return [{"key": m.metric_key, "name": m.metric_name, "value": m.value, "period": str(m.period_end)} for m in result.scalars().all()]

    async def _get_recent_reports(self, org_id: uuid.UUID, agent_type: str, limit: int = 5) -> list[dict]:
        result = await self.db.execute(
            select(BusinessReport).where(
                and_(
                    BusinessReport.organization_id == org_id,
                    BusinessReport.agent_type == agent_type,
                )
            ).order_by(BusinessReport.created_at.desc()).limit(limit)
        )
        return [{"title": r.title, "type": r.report_type, "summary": r.summary, "created": str(r.created_at)} for r in result.scalars().all()]

    async def _query_knowledge(self, org_id: uuid.UUID, query: str, limit: int = 5) -> list[dict]:
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                and_(
                    KnowledgeDocument.organization_id == org_id,
                    KnowledgeDocument.is_active == True,
                )
            ).limit(limit)
        )
        docs = result.scalars().all()
        if not docs:
            return []

        response = await ai_service.complete(
            prompt=(
                f"Given this user query: '{query}'\n\n"
                f"Score these knowledge documents by relevance (0-10). "
                f"Return JSON array: [{{\"id\": \"...\", \"title\": \"...\", \"score\": 0}}]\n\n"
                + "\n".join(f"[{d.id}] {d.title}: {d.content[:200]}" for d in docs)
            ),
        )
        text = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        try:
            scored = json.loads(text)
            scored.sort(key=lambda x: x.get("score", 0), reverse=True)
            top_ids = {s["id"] for s in scored[:limit] if s.get("score", 0) > 5}
            return [{"id": str(d.id), "title": d.title, "content": d.content[:500]} for d in docs if str(d.id) in top_ids]
        except (json.JSONDecodeError, KeyError, TypeError):
            return [{"id": str(d.id), "title": d.title, "content": d.content[:500]} for d in docs[:limit]]

    async def _extract_suggestions(self, text: str) -> list[str]:
        response = await ai_service.complete(
            prompt=f"Extract actionable recommendations from this text as a JSON array of strings:\n{text[:3000]}",
        )
        t = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        try:
            return json.loads(t) if isinstance(t, str) else t
        except (json.JSONDecodeError, TypeError):
            return []

    async def _store_metrics_from_suggestions(self, org_id: uuid.UUID, agent_type: str, suggestions: list[str]):
        for s in suggestions[:5]:
            metric = BusinessMetric(
                organization_id=org_id,
                agent_type=agent_type,
                metric_key="ai_suggestion",
                metric_name=s[:200],
                value=1.0,
                source="ai_generated",
            )
            self.db.add(metric)
        await self.db.flush()

    async def _parse_report_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        response = await ai_service.complete(
            prompt=f"Parse this business report into JSON with keys: summary, content, recommendations:\n{text[:5000]}",
        )
        t = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        try:
            return json.loads(t)
        except (json.JSONDecodeError, TypeError):
            return {"summary": text[:500], "content": {"raw": text}, "recommendations": []}


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_document(
        self, org_id: uuid.UUID, title: str, content: str,
        doc_type: str | None = None, source: str | None = None,
        tags: list[str] | None = None
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            organization_id=org_id,
            title=title,
            content=content,
            doc_type=doc_type,
            source=source,
            tags=tags or [],
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def query(self, org_id: uuid.UUID, query: str, limit: int = 5) -> list[dict]:
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                and_(
                    KnowledgeDocument.organization_id == org_id,
                    KnowledgeDocument.is_active == True,
                )
            ).limit(50)
        )
        docs = result.scalars().all()
        if not docs:
            return []

        response = await ai_service.complete(
            prompt=(
                f"Find the most relevant documents for: '{query}'\n\n"
                "Return JSON array of objects with 'id' and 'relevance_score' (0-10).\n"
                + "\n".join(f"ID={d.id} TITLE={d.title} CONTENT={d.content[:300]}" for d in docs)
            ),
        )
        text = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        try:
            scored = json.loads(text)
            scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            top = [s for s in scored if s.get("relevance_score", 0) >= 5][:limit]
            return [{"id": str(d.id), "title": d.title, "content": d.content, "type": d.doc_type} for d in docs if any(str(d.id) == s.get("id") for s in top)]
        except (json.JSONDecodeError, TypeError, KeyError):
            return [{"id": str(d.id), "title": d.title, "content": d.content[:500]} for d in docs[:limit]]

    async def delete_document(self, doc_id: uuid.UUID) -> bool:
        doc = await self.db.get(KnowledgeDocument, doc_id)
        if not doc:
            return False
        doc.is_active = False
        await self.db.flush()
        return True


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self, org_id: uuid.UUID, requester_id: uuid.UUID, request_type: str,
        title: str, description: str | None = None, priority: str = "medium",
        payload: dict | None = None
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            organization_id=org_id,
            request_type=request_type,
            title=title,
            description=description,
            requester_id=requester_id,
            priority=priority,
            payload=payload,
        )
        self.db.add(req)
        await self.db.flush()
        return req

    async def approve(self, request_id: uuid.UUID, approver_id: uuid.UUID, notes: str | None = None) -> ApprovalRequest:
        req = await self.db.get(ApprovalRequest, request_id)
        if not req:
            raise AppError(detail="Approval request not found")
        req.status = "approved"
        req.approver_id = approver_id
        req.decision_notes = notes
        req.decided_at = datetime.now(timezone.utc)
        await self.db.flush()
        return req

    async def reject(self, request_id: uuid.UUID, approver_id: uuid.UUID, reason: str) -> ApprovalRequest:
        req = await self.db.get(ApprovalRequest, request_id)
        if not req:
            raise AppError(detail="Approval request not found")
        req.status = "rejected"
        req.approver_id = approver_id
        req.decision_notes = reason
        req.decided_at = datetime.now(timezone.utc)
        await self.db.flush()
        return req

    async def list_pending(self, org_id: uuid.UUID) -> list[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest).where(
                and_(
                    ApprovalRequest.organization_id == org_id,
                    ApprovalRequest.status == "pending",
                )
            ).order_by(ApprovalRequest.created_at.desc())
        )
        return result.scalars().all()

    async def list_for_user(self, user_id: uuid.UUID, org_id: uuid.UUID) -> list[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest).where(
                and_(
                    ApprovalRequest.organization_id == org_id,
                    ApprovalRequest.requester_id == user_id,
                )
            ).order_by(ApprovalRequest.created_at.desc()).limit(50)
        )
        return result.scalars().all()


class FinancialAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_transaction(
        self, org_id: uuid.UUID, record_type: str, category: str,
        amount: float, description: str | None = None,
        currency: str = "USD", transaction_date: datetime | None = None,
        reference: str | None = None, donor: str | None = None,
        grant_code: str | None = None, budget_line: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> FinancialRecord:
        record = FinancialRecord(
            organization_id=org_id,
            record_type=record_type,
            category=category,
            amount=amount,
            description=description,
            currency=currency,
            transaction_date=transaction_date or datetime.now(timezone.utc),
            reference=reference,
            donor=donor,
            grant_code=grant_code,
            budget_line=budget_line,
            project_id=project_id,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_budget_summary(self, org_id: uuid.UUID, period_start: datetime, period_end: datetime) -> dict:
        income = await self.db.execute(
            select(func.sum(FinancialRecord.amount)).where(
                and_(
                    FinancialRecord.organization_id == org_id,
                    FinancialRecord.record_type == "income",
                    FinancialRecord.transaction_date.between(period_start, period_end),
                )
            )
        )
        expenses = await self.db.execute(
            select(func.sum(FinancialRecord.amount)).where(
                and_(
                    FinancialRecord.organization_id == org_id,
                    FinancialRecord.record_type == "expense",
                    FinancialRecord.transaction_date.between(period_start, period_end),
                )
            )
        )
        income_total = float(income.scalar() or 0)
        expense_total = float(expenses.scalar() or 0)

        cats = await self.db.execute(
            select(
                FinancialRecord.category,
                func.sum(FinancialRecord.amount),
                func.count(FinancialRecord.id),
            ).where(
                and_(
                    FinancialRecord.organization_id == org_id,
                    FinancialRecord.transaction_date.between(period_start, period_end),
                )
            ).group_by(FinancialRecord.category)
        )

        return {
            "total_income": income_total,
            "total_expenses": expense_total,
            "net": income_total - expense_total,
            "categories": {row[0]: {"amount": float(row[1]), "count": row[2]} for row in cats.all()},
        }

    async def forecast_budget(self, org_id: uuid.UUID, months: int = 12) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
        result = await self.db.execute(
            select(
                func.date_trunc("month", FinancialRecord.transaction_date).label("month"),
                func.sum(FinancialRecord.amount).label("total"),
                FinancialRecord.record_type,
            ).where(
                and_(
                    FinancialRecord.organization_id == org_id,
                    FinancialRecord.transaction_date >= cutoff,
                )
            ).group_by("month", FinancialRecord.record_type)
            .order_by("month")
        )
        rows = result.all()
        if not rows:
            return {"forecast": [], "message": "Insufficient data for forecasting"}

        response = await ai_service.complete(
            prompt=(
                f"Analyze this monthly financial data and forecast the next {months} months. "
                f"Return JSON with 'forecast' (array of monthly projections with month, income, expense, net) "
                f"and 'insights' (key trends and recommendations).\nData:\n"
                + json.dumps([{"month": str(r.month), "type": r.record_type, "total": float(r.total)} for r in rows], default=str)
            ),
        )
        text = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"forecast": [], "insights": "Could not parse forecast"}


class BusinessWorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(
        self, org_id: uuid.UUID, name: str, workflow_type: str,
        trigger: str, steps: list[dict]
    ) -> BusinessWorkflow:
        wf = BusinessWorkflow(
            organization_id=org_id,
            name=name,
            workflow_type=workflow_type,
            trigger=trigger,
            steps=steps,
        )
        self.db.add(wf)
        await self.db.flush()
        return wf

    async def execute_workflow(
        self, workflow_id: uuid.UUID, org_id: uuid.UUID, input_data: dict | None = None
    ) -> BusinessWorkflowExecution:
        wf = await self.db.get(BusinessWorkflow, workflow_id)
        if not wf:
            raise AppError(detail="Workflow not found")

        execution = BusinessWorkflowExecution(
            workflow_id=workflow_id,
            organization_id=org_id,
            status="running",
            current_step=0,
            total_steps=len(wf.steps),
            input_data=input_data,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(execution)
        await self.db.flush()

        try:
            result = await self._run_steps(wf.steps, input_data or {}, execution.id)
            execution.output_data = result
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            wf.last_run_at = datetime.now(timezone.utc)
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)

        await self.db.flush()
        return execution

    async def _run_steps(self, steps: list[dict], input_data: dict, execution_id: uuid.UUID) -> dict:
        context = dict(input_data)
        for i, step in enumerate(steps):
            step_type = step.get("type", "action")
            if step_type == "ai_query":
                context = await self._step_ai_query(step, context)
            elif step_type == "condition":
                context = self._step_condition(step, context)
            elif step_type == "approval":
                context = await self._create_approval_step(step, context, execution_id)
            elif step_type == "notification":
                context = self._step_notification(step, context)

            await self.db.execute(
                select(BusinessWorkflowExecution).where(BusinessWorkflowExecution.id == execution_id)
            )
        return context

    async def _step_ai_query(self, step: dict, context: dict) -> dict:
        prompt = step.get("prompt", "")
        for k, v in context.items():
            prompt = prompt.replace(f"{{{{{k}}}}}", str(v))
        response = await ai_service.complete(prompt=prompt)
        text = response if isinstance(response, str) else response.get("content", response.get("text", ""))
        context[step.get("output_key", "ai_result")] = text
        return context

    def _step_condition(self, step: dict, context: dict) -> dict:
        field = step.get("field", "")
        operator = step.get("operator", "equals")
        value = step.get("value")
        actual = context.get(field)
        if operator == "equals" and str(actual) == str(value):
            context["condition_met"] = True
        elif operator == "greater_than" and actual and value and actual > value:
            context["condition_met"] = True
        elif operator == "less_than" and actual and value and actual < value:
            context["condition_met"] = True
        else:
            context["condition_met"] = False
        return context

    async def _create_approval_step(self, step: dict, context: dict, execution_id: uuid.UUID) -> dict:
        context["approval_required"] = True
        context["approval_reason"] = step.get("reason", "Approval required")
        return context

    def _step_notification(self, step: dict, context: dict) -> dict:
        context["notification_sent"] = True
        context["notification_message"] = step.get("message", "")
        return context
