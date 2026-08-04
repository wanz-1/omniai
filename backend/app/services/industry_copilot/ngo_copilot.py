from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import ai_service

class NGOCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def analyze_grant(self, grant_description):
        p = f"""Analyze this grant opportunity:
{grant_description}
Provide: eligibility, deadline, funding amount, requirements, success probability, recommended next steps."""
        return await ai_service.complete(p)

    async def draft_proposal(self, org_info, grant_info):
        p = f"""Draft a grant proposal.
Organization: {org_info}
Grant: {grant_info}
Generate: executive summary, problem statement, methodology, budget outline, expected outcomes."""
        return await ai_service.complete(p)

    async def generate_report(self, report_type, data):
        p = f"""Generate a {report_type} for an NGO.
Data: {data}
Include: narrative summary, achievements, challenges, financial overview, recommendations."""
        return await ai_service.complete(p)

    async def create_logframe(self, objectives, activities):
        p = f"""Create a logical framework.
Objectives: {objectives}
Activities: {activities}
Produce: goal, purpose, outputs, activities, indicators, means of verification, assumptions."""
        return await ai_service.complete(p)

    async def check_donor_compliance(self, donor_requirements, proposal):
        p = f"""Check compliance with donor requirements.
Requirements: {donor_requirements}
Proposal: {proposal}
Identify gaps, non-compliance issues, and recommendations."""
        return await ai_service.complete(p)
