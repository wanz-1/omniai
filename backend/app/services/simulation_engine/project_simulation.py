from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service


class ProjectSimulation:
    def __init__(self, db: AsyncSession): self.db = db

    async def simulate_project(self, organization_id, project_data, scenario):
        prompt = f"""Simulate this project under the given scenario.
Project data: {project_data}
Scenario: {scenario}
Analyze: timeline impact, budget changes, resource gaps, risk factors, alternative paths.
Provide: adjusted timeline, cost impact, risk assessment, recommendations."""
        return await ai_service.complete(prompt)

    async def resource_impact(self, organization_id, project_data, resource_change):
        prompt = f"""Analyze resource impact on project.
Project: {project_data}
Resource change: {resource_change}
Assess: schedule delays, cost overruns, quality impact, scope changes, mitigation strategies."""
        return await ai_service.complete(prompt)

    async def timeline_what_if(self, organization_id, project_plan, delay_scenario):
        prompt = f"""Run timeline what-if analysis.
Project plan: {project_plan}
Delay scenario: {delay_scenario}
Analyze: critical path impact, cascading delays, cost implications, recovery options."""
        return await ai_service.complete(prompt)
