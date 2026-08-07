import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service

DEBUG_SYSTEM_PROMPT = """You are an expert AI Debugger. Analyze errors and provide:
1. Root cause analysis
2. Fix/solution
3. Corrected code
4. Prevention suggestions

Analyze the error message, code context, and provide a complete debug solution.
Respond in JSON format:
{
  "root_cause": "detailed explanation of what caused the error",
  "solution": "step-by-step fix instructions",
  "fixed_code": "the corrected code",
  "suggestions": ["prevention tip 1", "prevention tip 2"]
}"""


class CodeDebuggerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def debug(
        self,
        code: str | None = None,
        error_message: str | None = None,
        language: str = "python",
        context: str | None = None,
    ) -> dict:
        user_content = f"Language: {language}\n"
        if error_message:
            user_content += f"Error: {error_message}\n"
        if code:
            user_content += f"Code:\n{code}\n"
        if context:
            user_content += f"Context:\n{context}\n"

        messages = [
            {"role": "system", "content": DEBUG_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.2)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {
                "root_cause": "Analysis completed",
                "solution": result.get("content", "Review the code for errors"),
                "fixed_code": code or "",
                "suggestions": ["Review your code logic", "Add input validation", "Use try/catch blocks"],
            }

    async def review_code(self, code: str, language: str = "python") -> dict:
        messages = [
            {"role": "system", "content": f"You are a code reviewer. Analyze {language} code for bugs, security issues, and improvements."},
            {"role": "user", "content": f"Review this {language} code:\n\n{code}\n\nProvide: issues found, severity, and fix recommendations as JSON."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"issues": [{"description": result.get("content", ""), "severity": "info"}]}
