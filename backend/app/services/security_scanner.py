import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import SecurityScan, StudioFile, StudioProject
from app.services.ai_service import ai_service


SECURITY_SYSTEM_PROMPT = """You are an expert Security Engineer AI. Perform a comprehensive security scan:
1. Check for OWASP Top 10 vulnerabilities
2. Analyze authentication/authorization
3. Check for injection flaws (SQL, XSS, command)
4. Review data handling and encryption
5. Check dependency risks
6. Review configuration security

Respond in JSON:
{
  "risk_score": 0-100,
  "summary": "overall security assessment",
  "vulnerabilities": [{"type": "SQL Injection", "severity": "critical", "file": "src/db.py", "line": 45, "description": "...", "fix": "..."}],
  "recommendations": ["Use parameterized queries", "Add input validation"],
  "severity_counts": {"critical": 1, "high": 2, "medium": 3, "low": 5}
}"""


class SecurityScannerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_project(self, project_id: uuid.UUID, scan_type: str = "full", user_id: uuid.UUID | None = None) -> SecurityScan:
        result = await self.db.execute(select(StudioProject).where(StudioProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        files_result = await self.db.execute(
            select(StudioFile).where(StudioFile.project_id == project_id)
        )
        files = list(files_result.scalars().all())

        code_context = "\n\n".join([f"--- {f.path} ---\n{f.content[:3000]}" for f in files[:8]])

        scan = SecurityScan(
            scan_type=scan_type,
            status="in_progress",
            project_id=project_id,
            user_id=user_id,
        )
        self.db.add(scan)
        await self.db.flush()

        messages = [
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {"role": "user", "content": f"Security scan for {project.name} ({project.language})\n\nCode:\n{code_context}\n\nProvide complete security analysis as JSON."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.2)
        try:
            scan_data = json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            scan_data = {
                "risk_score": 50,
                "summary": result.get("content", "Security scan completed"),
                "vulnerabilities": [],
                "recommendations": ["Review code manually"],
                "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }

        scan.status = "completed"
        scan.risk_score = scan_data.get("risk_score", 0)
        scan.vulnerabilities = scan_data.get("vulnerabilities", [])
        scan.summary = scan_data.get("summary", "")
        scan.recommendations = scan_data.get("recommendations", [])
        scan.severity_counts = scan_data.get("severity_counts", {})
        scan.report = json.dumps(scan_data, indent=2)

        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    async def get_vulnerability_count(self, project_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(SecurityScan)
            .where(SecurityScan.project_id == project_id)
            .order_by(SecurityScan.created_at.desc())
            .limit(1)
        )
        scan = result.scalar_one_or_none()
        if scan and scan.severity_counts:
            return {
                "total": sum(scan.severity_counts.values()),
                "critical": scan.severity_counts.get("critical", 0),
                "high": scan.severity_counts.get("high", 0),
                "medium": scan.severity_counts.get("medium", 0),
                "low": scan.severity_counts.get("low", 0),
            }
        return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
