import asyncio
import json
import logging
import time
import uuid
from datetime import timezone
from pathlib import Path
from typing import AsyncGenerator

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.agent import (
    AgentAnalytics,
    AgentExecution,
    AgentMemory,
    AgentProfile,
    AgentSkill,
    AgentTask,
    AgentTool,
    Workflow,
    WorkflowStep,
)
from app.schemas.agent import AgentChatResponse, AgentTaskResponse
from app.services.ai_service import ai_service

logger = logging.getLogger("omniai.agent.tools")


class ToolExecutor:
    async def execute(self, tool: AgentTool, params: dict) -> str:
        tool_type = tool.tool_type
        config = tool.config or {}

        try:
            if tool_type == "web_search":
                return await self._web_search(params.get("query", ""))
            elif tool_type == "web_scrape":
                return await self._web_scrape(params.get("url", ""))
            elif tool_type == "document_read":
                return await self._document_read(params.get("path", ""))
            elif tool_type == "document_write":
                return await self._document_write(params.get("path", ""), params.get("content", ""))
            elif tool_type == "data_analysis":
                data = params.get("data", "")
                analysis_type = params.get("type", "summary")
                return await self._analyze_data(data, analysis_type)
            elif tool_type == "chart_creation":
                return await self._create_chart(params)
            elif tool_type == "code_execution":
                return await self._execute_code(params.get("code", ""), params.get("language", "python"))
            elif tool_type == "api_call":
                return await self._api_call(params.get("url", ""), params.get("method", "GET"), params.get("headers", {}), params.get("body", {}))
            elif tool_type == "email":
                return await self._send_email(params.get("to", ""), params.get("subject", ""), params.get("body", ""))
            elif tool_type == "file_system":
                return await self._file_system(params.get("action", "read"), params.get("path", ""), params.get("content", ""))
            elif tool_type == "image_generation":
                return await self._generate_image(params.get("prompt", ""), params)
            elif tool_type == "database":
                return await self._database_query(params.get("query", ""), params)
            elif tool_type == "slack":
                return await self._slack_action(params)
            elif tool_type == "github":
                return await self._github_action(params)
            elif tool_type == "google_drive":
                return await self._google_drive_action(params)
            elif tool_type == "crm":
                return await self._crm_action(params)
            elif tool_type == "custom":
                return await self._custom_api_call(config.get("endpoint", ""), params)
            return f"[Unknown tool: {tool_type}]"
        except Exception as e:
            logger.error("Tool execution failed", extra={"tool": tool_type, "error": str(e)})
            return f"[Tool error: {tool_type} - {str(e)}]"

    async def _web_search(self, query: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                )
                if r.is_success:
                    data = r.json()
                    abstract = data.get("AbstractText", "")
                    results = data.get("RelatedTopics", [])[:5]
                    if abstract:
                        return abstract
                    if results:
                        return "\n".join(
                            r.get("Text", "") for r in results if isinstance(r, dict)
                        )
            return f"Search results for '{query}': No results found via primary source."
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                r = await client.get(f"https://lite.duckduckgo.com/lite/?q={query}")
                if r.is_success:
                    import re
                    snippets = re.findall(r'class="result-snippet">(.*?)</td>', r.text)
                    if snippets:
                        return "\n".join(s.strip() for s in snippets[:5])
        except Exception:
            pass

        response = await ai_service.complete(
            messages=[{"role": "user", "content": f"Provide a concise answer to: {query}"}],
            model="gpt-4o-mini", temperature=0.3,
        )
        return response.get("content", f"Search results for '{query}' unavailable.")

    async def _web_scrape(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: {url}"
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; OmniAI/1.0)"})
                r.raise_for_status()
                import re
                text = re.sub(r'<[^>]+>', ' ', r.text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:5000]
        except Exception as e:
            return f"Scrape failed for {url}: {str(e)}"

    async def _analyze_data(self, data: str, analysis_type: str) -> str:
        messages = [
            {"role": "system", "content": f"You are a data analysis assistant. Perform {analysis_type} analysis on the provided data."},
            {"role": "user", "content": f"Data:\n{data[:8000]}\n\nProvide {analysis_type} analysis with insights and recommendations."},
        ]
        response = await ai_service.complete(messages=messages, temperature=0.3)
        return response["content"]

    async def _create_chart(self, params: dict) -> str:
        chart_type = params.get("type", "bar")
        labels = params.get("labels", [])
        values = params.get("values", [])
        title = params.get("title", "Chart")
        import json as _json
        chart_data = {
            "type": chart_type,
            "data": {"labels": labels, "datasets": [{"label": title, "data": values}]},
            "options": {"title": {"display": True, "text": title}},
        }
        html = f"""<div style="max-width:600px;margin:auto;">
<canvas id="chart-{uuid.uuid4().hex[:8]}"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('chart-{uuid.uuid4().hex[:8]}'), {_json.dumps(chart_data)});
</script>
</div>"""
        return html

    async def _execute_code(self, code: str, language: str) -> str:
        if language == "python":
            try:
                restricted_globals = {"__builtins__": {"print": print, "len": len, "range": range, "list": list, "dict": dict, "str": str, "int": int, "float": float, "bool": bool, "tuple": tuple, "set": set, "enumerate": enumerate, "zip": zip, "map": map, "filter": filter, "sum": sum, "min": min, "max": max, "abs": abs, "round": round, "sorted": sorted, "reversed": reversed, "type": type, "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr, "setattr": setattr, "ValueError": ValueError, "TypeError": TypeError, "KeyError": KeyError, "IndexError": IndexError, "Exception": Exception}}
                local_vars = {}
                exec(code, restricted_globals, local_vars)
                result = str(local_vars.get("result", local_vars.get("output", "Code executed successfully (no output)")))
                return result[:2000]
            except Exception as e:
                return f"Execution Error: {str(e)}"
        return f"Code execution for {language} is not supported in sandbox mode."

    async def _api_call(self, url: str, method: str, headers: dict, body: dict) -> str:
        if not url:
            return "No URL provided for API call"
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                r = await client.request(method.upper(), url, headers=headers, json=body if body else None)
                r.raise_for_status()
                text = r.text[:3000]
                return f"Status: {r.status_code}\nResponse: {text}"
        except Exception as e:
            return f"API call failed: {str(e)}"

    async def _file_system(self, action: str, path: str, content: str = "") -> str:
        import os
        safe_path = os.path.normpath(path) if path else ""
        if not safe_path:
            return "No path specified"
        try:
            if action == "read":
                if os.path.exists(safe_path):
                    with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read(5000)
                return f"File not found: {safe_path}"
            elif action == "write":
                os.makedirs(os.path.dirname(safe_path) or ".", exist_ok=True)
                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Written {len(content)} bytes to {safe_path}"
            elif action == "list":
                if os.path.isdir(safe_path):
                    entries = os.listdir(safe_path)
                    return "\n".join(entries[:50])
                return f"Not a directory: {safe_path}"
            elif action == "delete":
                if os.path.exists(safe_path):
                    if os.path.isdir(safe_path):
                        import shutil
                        shutil.rmtree(safe_path)
                    else:
                        os.remove(safe_path)
                    return f"Deleted: {safe_path}"
                return f"Not found: {safe_path}"
            return f"Unsupported action: {action}"
        except Exception as e:
            return f"File system error: {str(e)}"

    async def _generate_image(self, prompt: str, params: dict) -> str:
        if not prompt:
            return "No prompt provided for image generation"
        try:
            response = await ai_service.complete(
                messages=[{"role": "user", "content": f"Generate a detailed image generation prompt: {prompt}"}],
                model="gpt-4o-mini", temperature=0.7,
            )
            enhanced = response.get("content", prompt)
            return f"[Image generation prompt: {enhanced[:200]}...]\nNote: Image generation requires DALL-E, Stable Diffusion, or similar API configured."
        except Exception as e:
            return f"Image generation error: {str(e)}"

    async def _database_query(self, query: str, params: dict) -> str:
        return f"[Database query analyzed: {query[:200]}...\nExecution requires a configured database connection.]"

    async def _slack_action(self, params: dict) -> str:
        token = params.get("token", "")
        if not token:
            return "Slack token not configured"
        action = params.get("action", "send_message")
        channel = params.get("channel", "")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if action == "send_message":
                    r = await client.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"channel": channel, "text": params.get("message", "")},
                    )
                    r.raise_for_status()
                    data = r.json()
                    if data.get("ok"):
                        return f"Message sent to #{channel}"
                    return f"Slack error: {data.get('error', 'unknown')}"
                if action == "list_channels":
                    r = await client.get("https://slack.com/api/conversations.list?limit=50", headers={"Authorization": f"Bearer {token}"})
                    r.raise_for_status()
                    data = r.json()
                    channels = [c["name"] for c in data.get("channels", [])]
                    return f"Available channels: {', '.join(channels[:20])}"
        except Exception as e:
            return f"Slack error: {str(e)}"
        return "Slack action completed"

    async def _github_action(self, params: dict) -> str:
        token = params.get("token", "")
        if not token:
            return "GitHub token not configured"
        action = params.get("action", "list_repos")
        repo = params.get("repo", "")
        try:
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                if action == "list_repos":
                    r = await client.get("https://api.github.com/user/repos?per_page=30", headers=headers)
                    r.raise_for_status()
                    repos = [r["full_name"] for r in r.json()]
                    return f"Repositories: {', '.join(repos[:15])}"
                if action == "list_issues":
                    r = await client.get(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=20", headers=headers)
                    r.raise_for_status()
                    issues = [f"#{i['number']} {i['title']}" for i in r.json()]
                    return f"Issues: {', '.join(issues[:15])}" if issues else "No open issues"
                if action == "get_readme":
                    r = await client.get(f"https://api.github.com/repos/{repo}/readme", headers={**headers, "Accept": "application/vnd.github.raw+json"})
                    r.raise_for_status()
                    return r.text[:2000]
        except Exception as e:
            return f"GitHub error: {str(e)}"
        return "GitHub action completed"

    async def _google_drive_action(self, params: dict) -> str:
        token = params.get("token", "")
        if not token:
            return "Google Drive token not configured"
        action = params.get("action", "list_files")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                if action == "list_files":
                    r = await client.get("https://www.googleapis.com/drive/v3/files?pageSize=20", headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    files = [f"{f['name']} ({f.get('mimeType', 'unknown')})" for f in data.get("files", [])]
                    return f"Files: {', '.join(files[:15])}" if files else "No files found"
                if action == "search":
                    query = params.get("query", "")
                    r = await client.get(f"https://www.googleapis.com/drive/v3/files?q=name contains '{query}'", headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    files = [f["name"] for f in data.get("files", [])]
                    return f"Search results for '{query}': {', '.join(files[:10])}" if files else f"No results for '{query}'"
        except Exception as e:
            return f"Google Drive error: {str(e)}"
        return "Google Drive action completed"

    async def _custom_api_call(self, endpoint: str, params: dict) -> str:
        if not endpoint:
            return "No endpoint configured for custom tool"
        try:
            headers = params.get("headers", {})
            body = params.get("body", params)
            method = params.get("method", "POST")
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.request(method, endpoint, headers=headers, json=body)
                r.raise_for_status()
                return r.text[:2000]
        except Exception as e:
            return f"Custom API call error: {str(e)}"

    def _workspace_path(self, path: str) -> Path | None:
        workspace = Path(settings.agent_workspace_dir).resolve()
        target = (workspace / path).resolve()
        if str(target).startswith(str(workspace)):
            return target
        return None

    async def _document_read(self, path: str) -> str:
        target = self._workspace_path(path)
        if target is None:
            return "[Permission denied: path escapes agent workspace]"
        if not target.is_file():
            return f"[Document not found: {path}]"
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > 20000:
            content = content[:20000] + "\n...[truncated]"
        return content

    async def _document_write(self, path: str, content: str) -> str:
        target = self._workspace_path(path)
        if target is None:
            return "[Permission denied: path escapes agent workspace]"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content or "", encoding="utf-8")
        except OSError as e:
            return f"[Document write failed: {str(e)}]"
        return f"[Document written: {path} ({len(content or '')} chars)]"

    async def _send_email(self, to: str, subject: str, body: str) -> str:
        if not to or "@" not in to:
            return "[Email error: no valid recipient provided]"
        if not settings.smtp_host:
            return f"[Email queued to {to}: {subject}] (SMTP not configured; set SMTP_HOST to send)"
        try:
            def _smtp_send() -> None:
                import smtplib
                from email.mime.text import MIMEText

                msg = MIMEText(body or "", "plain", "utf-8")
                msg["Subject"] = subject or "(no subject)"
                msg["From"] = settings.smtp_from_email or settings.smtp_username or "omniai@localhost"
                msg["To"] = to
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    if settings.smtp_username and settings.smtp_password:
                        server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)

            await asyncio.to_thread(_smtp_send)
        except Exception as e:
            return f"[Email error: {str(e)}]"
        return f"[Email sent to {to}: {subject}]"

    async def _crm_action(self, params: dict) -> str:
        action = params.get("action", "query")
        supported = {"query", "add_contact", "update_contact", "list_contacts"}
        if action not in supported:
            return f"[CRM error: unsupported action '{action}']"
        name = params.get("name", params.get("contact", ""))
        email = params.get("email", "")
        if action in ("add_contact", "update_contact") and (not name or not email):
            return "[CRM error: 'name' and 'email' are required for this action]"
        summary = {
            "status": "ok",
            "action": action,
            "entity": "contact",
            "name": name,
            "email": email,
            "note": "CRM persistence requires a connected CRM integration (see Connector Platform > CRM)",
        }
        return json.dumps(summary, ensure_ascii=False)


class MemoryManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def remember(self, agent_id: uuid.UUID, key: str, content: str, memory_type: str = "fact", category: str | None = None, importance: int = 1, user_id: uuid.UUID | None = None):
        existing = await self.db.execute(
            select(AgentMemory).where(AgentMemory.agent_id == agent_id, AgentMemory.key == key)
        )
        memory = existing.scalar_one_or_none()
        if memory:
            memory.content = content
            memory.importance = importance
        else:
            memory = AgentMemory(agent_id=agent_id, key=key, content=content, memory_type=memory_type, category=category, importance=importance, user_id=user_id)
            self.db.add(memory)
        await self.db.flush()
        return memory

    async def recall(self, agent_id: uuid.UUID, query: str, limit: int = 10) -> list[AgentMemory]:
        result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .order_by(AgentMemory.importance.desc(), AgentMemory.updated_at.desc())
            .limit(limit)
        )
        memories = result.scalars().all()
        if not memories:
            return []
        messages = [
            {"role": "system", "content": "Given a query and list of memories, return the indices of relevant memories (0-based). Return as JSON array."},
            {"role": "user", "content": f"Query: {query}\n\nMemories:\n" + "\n".join(f"[{i}] {m.key}: {m.content[:200]}" for i, m in enumerate(memories))},
        ]
        response = await ai_service.complete(messages=messages, temperature=0.1)
        try:
            indices = json.loads(response["content"])
            return [memories[i] for i in indices if isinstance(i, int) and i < len(memories)]
        except (json.JSONDecodeError, TypeError, IndexError):
            return memories[:3]

    async def forget(self, agent_id: uuid.UUID, key: str):
        result = await self.db.execute(
            select(AgentMemory).where(AgentMemory.agent_id == agent_id, AgentMemory.key == key)
        )
        memory = result.scalar_one_or_none()
        if memory:
            await self.db.delete(memory)
            await self.db.flush()

    async def build_context(self, agent_id: uuid.UUID, query: str) -> str:
        memories = await self.recall(agent_id, query, limit=8)
        if not memories:
            return ""
        return "\n".join(f"- {m.key}: {m.content}" for m in memories)


class WorkflowEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tool_executor = ToolExecutor()

    async def execute_workflow(self, workflow: Workflow, trigger_data: dict) -> AsyncGenerator[dict, None]:
        steps_result = await self.db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id).order_by(WorkflowStep.order)
        )
        steps = steps_result.scalars().all()

        ctx = dict(trigger_data)
        for step in steps:
            yield {"type": "step_start", "step": step.name, "step_type": step.step_type}

            if step.step_type == "ai_decision":
                prompt = step.config.get("prompt", "Make a decision based on context.")
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Context: {json.dumps(ctx)}"},
                ]
                response = await ai_service.complete(messages=messages, temperature=0.3)
                ctx["decision"] = response["content"]
                yield {"type": "decision", "content": response["content"], "step": step.name}

            elif step.step_type == "condition":
                condition = step.config.get("condition", "")
                messages = [
                    {"role": "system", "content": "Evaluate if this condition is true or false based on context. Respond with only 'true' or 'false'."},
                    {"role": "user", "content": f"Condition: {condition}\nContext: {json.dumps(ctx)}"},
                ]
                response = await ai_service.complete(messages=messages, temperature=0.1)
                ctx["condition_result"] = response["content"].strip().lower() == "true"
                yield {"type": "condition", "result": ctx["condition_result"], "step": step.name}

            elif step.step_type == "action":
                action_type = step.config.get("action_type", "message")
                content = step.config.get("content", "")
                rendered = content
                for k, v in ctx.items():
                    rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
                ctx["action_result"] = rendered
                yield {"type": "action", "action_type": action_type, "content": rendered, "step": step.name}

            elif step.step_type == "tool_call":
                tool_name = step.config.get("tool_name", "")
                params = step.config.get("params", {})
                resolved_params = {}
                for k, v in params.items():
                    if isinstance(v, str):
                        for ck, cv in ctx.items():
                            v = v.replace(f"{{{{{ck}}}}}", str(cv))
                    resolved_params[k] = v

                tools_result = await self.db.execute(
                    select(AgentTool).where(AgentTool.agent_id == workflow.agent_id, AgentTool.name == tool_name)
                )
                tool = tools_result.scalar_one_or_none()
                if tool:
                    result = await self.tool_executor.execute(tool, resolved_params)
                    ctx["tool_result"] = result
                    yield {"type": "tool_result", "tool": tool_name, "result": result, "step": step.name}

            elif step.step_type == "notification":
                message = step.config.get("message", "")
                for k, v in ctx.items():
                    message = message.replace(f"{{{{{k}}}}}", str(v))
                yield {"type": "notification", "message": message, "step": step.name}

            elif step.step_type == "human_approval":
                yield {"type": "human_approval_required", "step": step.name, "config": step.config}
                return

            elif step.step_type == "delay":
                seconds = step.config.get("seconds", 1)
                yield {"type": "delay", "seconds": seconds, "step": step.name}

            elif step.step_type == "api_call":
                url = step.config.get("url", "")
                method = step.config.get("method", "GET")
                yield {"type": "api_call", "url": url, "method": method, "step": step.name}

            yield {"type": "step_complete", "step": step.name}

        yield {"type": "workflow_complete", "context": ctx}


class AgentOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tool_executor = ToolExecutor()
        self.memory_manager = MemoryManager(db)
        self.workflow_engine = WorkflowEngine(db)

    async def _get_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> AgentProfile:
        agent = await self.db.get(AgentProfile, agent_id)
        if not agent or (agent.user_id != user_id and not agent.is_template and not agent.marketplace_listed):
            raise NotFoundError("Agent", str(agent_id))
        return agent

    async def _get_skills_context(self, agent_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(AgentSkill).where(AgentSkill.agent_id == agent_id).order_by(AgentSkill.name)
        )
        skills = result.scalars().all()
        if not skills:
            return ""
        return "Skills:\n" + "\n".join(f"- {s.name}: {s.description or ''} (proficiency: {s.proficiency}/10)" for s in skills)

    async def _get_tools_context(self, agent_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(AgentTool).where(AgentTool.agent_id == agent_id, AgentTool.enabled == True)
        )
        tools = result.scalars().all()
        if not tools:
            return ""
        return "Available tools:\n" + "\n".join(f"- {t.name} ({t.tool_type}): {t.description or ''}" for t in tools)

    async def chat(self, agent_id: uuid.UUID, user_id: uuid.UUID, message: str) -> AgentChatResponse:
        agent = await self._get_agent(agent_id, user_id)
        skills_ctx = await self._get_skills_context(agent_id)
        tools_ctx = await self._get_tools_context(agent_id)
        memory_ctx = await self.memory_manager.build_context(agent_id, message)
        workflows_result = await self.db.execute(
            select(Workflow).where(Workflow.agent_id == agent_id, Workflow.is_active == True)
        )
        workflows = workflows_result.scalars().all()

        system = agent.system_prompt or f"You are a {agent.role} assistant."
        system += f"\n\nRole: {agent.role}\nDescription: {agent.description or ''}"
        if skills_ctx:
            system += f"\n\n{skills_ctx}"
        if tools_ctx:
            system += f"\n\n{tools_ctx}"
        if memory_ctx:
            system += f"\n\nRelevant memories:\n{memory_ctx}"
        if workflows:
            system += "\n\nActive workflows:\n" + "\n".join(f"- {w.name}: {w.description or ''}" for w in workflows)
        system += "\n\nYou can break down complex tasks into steps, use available tools, and reference past conversations. Be proactive and autonomous."

        start = time.perf_counter()
        response = await ai_service.complete(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
            model=agent.model,
            temperature=agent.temperature,
        )
        latency = int((time.perf_counter() - start) * 1000)

        await self.memory_manager.remember(
            agent_id, f"conversation_{int(time.time())}",
            f"User: {message}\nAssistant: {response['content'][:500]}",
            memory_type="conversation", importance=3, user_id=user_id,
        )

        execution = AgentExecution(
            agent_id=agent_id, user_id=user_id,
            status="completed", input=message[:500], output=response["content"][:500],
            duration_ms=latency, tokens_used=response.get("tokens_used", 0),
            steps_completed=1, steps_total=1,
        )
        self.db.add(execution)
        await self.db.flush()

        await self._update_analytics(agent_id, response.get("tokens_used", 0), latency)

        return AgentChatResponse(
            reply=response["content"],
            tokens_used=response.get("tokens_used", 0),
            execution_id=execution.id,
        )

    async def chat_stream(self, agent_id: uuid.UUID, user_id: uuid.UUID, message: str) -> AsyncGenerator[dict, None]:
        agent = await self._get_agent(agent_id, user_id)
        skills_ctx = await self._get_skills_context(agent_id)
        tools_ctx = await self._get_tools_context(agent_id)
        memory_ctx = await self.memory_manager.build_context(agent_id, message)

        system = agent.system_prompt or f"You are a {agent.role} assistant."
        system += f"\n\nRole: {agent.role}\nDescription: {agent.description or ''}"
        if skills_ctx:
            system += f"\n\n{skills_ctx}"
        if tools_ctx:
            system += f"\n\n{tools_ctx}"
        if memory_ctx:
            system += f"\n\nRelevant memories:\n{memory_ctx}"

        full_content = ""
        yield {"type": "planning", "content": "Analyzing request..."}
        stream = ai_service.complete_stream(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
            model=agent.model,
            temperature=agent.temperature,
        )
        async for token in stream:
            full_content += token
            yield {"type": "token", "content": token}

        await self.memory_manager.remember(
            agent_id, f"conversation_{int(time.time())}",
            f"User: {message}\nAssistant: {full_content[:500]}",
            memory_type="conversation", importance=3, user_id=user_id,
        )

        execution = AgentExecution(
            agent_id=agent_id, user_id=user_id,
            status="completed", input=message[:500], output=full_content[:500],
            tokens_used=0, steps_completed=1, steps_total=1,
        )
        self.db.add(execution)
        await self.db.flush()

        yield {"type": "complete", "execution_id": str(execution.id)}

    async def execute_task(self, agent_id: uuid.UUID, task_id: uuid.UUID, user_id: uuid.UUID) -> AgentTaskResponse:
        agent = await self._get_agent(agent_id, user_id)
        task = await self.db.get(AgentTask, task_id)
        if not task or task.agent_id != agent_id:
            raise NotFoundError("Task", str(task_id))

        task.status = "planning"
        await self.db.flush()

        skills_ctx = await self._get_skills_context(agent_id)
        tools_ctx = await self._get_tools_context(agent_id)
        memory_ctx = await self.memory_manager.build_context(agent_id, task.title)

        system = agent.system_prompt or f"You are a {agent.role} assistant."
        system += f"\n\nRole: {agent.role}\nDescription: {agent.description or ''}"
        if skills_ctx:
            system += f"\n\n{skills_ctx}"
        if tools_ctx:
            system += f"\n\n{tools_ctx}"
        if memory_ctx:
            system += f"\n\nRelevant memories:\n{memory_ctx}"
        system += "\n\nFor the given task, create an execution plan with steps. Then execute each step and provide the final result."

        start = time.perf_counter()
        response = await ai_service.complete(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": f"Task: {task.title}\nDescription: {task.description or ''}\nInput: {json.dumps(task.input_data or {})}"}],
            model=agent.model,
            temperature=agent.temperature,
        )
        latency = int((time.perf_counter() - start) * 1000)

        task.status = "completed"
        task.progress = 1.0
        task.result = response["content"]
        task.output_data = {"result": response["content"]}
        task.completed_at = __import__("datetime").datetime.now(timezone.utc)
        await self.db.flush()

        await self._update_analytics(agent_id, response.get("tokens_used", 0), latency)

        return AgentTaskResponse(
            id=task.id, title=task.title, description=task.description,
            status=task.status, priority=task.priority, progress=task.progress,
            result=task.result, error=task.error,
            input_data=task.input_data, output_data=task.output_data,
            execution_plan=task.execution_plan,
            agent_id=task.agent_id, user_id=task.user_id,
            parent_task_id=task.parent_task_id,
            started_at=task.started_at, completed_at=task.completed_at,
            created_at=task.created_at,
        )

    async def _update_analytics(self, agent_id: uuid.UUID, tokens: int, duration_ms: int):
        result = await self.db.execute(
            select(AgentAnalytics).where(AgentAnalytics.agent_id == agent_id)
        )
        analytics = result.scalar_one_or_none()
        if analytics:
            analytics.total_tasks += 1
            analytics.completed_tasks += 1
            analytics.total_tokens += tokens
            if analytics.avg_duration_ms:
                analytics.avg_duration_ms = (analytics.avg_duration_ms * (analytics.total_tasks - 1) + duration_ms) / analytics.total_tasks
            else:
                analytics.avg_duration_ms = float(duration_ms)
            await self.db.flush()
