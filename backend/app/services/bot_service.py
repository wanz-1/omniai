import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.bot import Bot, BotConversation, BotMessage
from app.schemas.bot import BotDeployRequest, BotTestRequest, BotTestResponse, BotTrainRequest
from app.services.ai_service import ai_service


class BotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def train(self, bot_id: uuid.UUID, user_id: uuid.UUID, body: BotTrainRequest) -> str:
        bot = await self.db.get(Bot, bot_id)
        if not bot or bot.user_id != user_id:
            raise NotFoundError("Bot", str(bot_id))

        kb_config = {"files": body.files or [], "urls": body.urls or [], "text": body.text or ""}
        bot.knowledge_base_config = kb_config
        await self.db.flush()
        return str(uuid.uuid4())

    async def test(self, bot_id: uuid.UUID, user_id: uuid.UUID, body: BotTestRequest) -> BotTestResponse:
        bot = await self.db.get(Bot, bot_id)
        if not bot or bot.user_id != user_id:
            raise NotFoundError("Bot", str(bot_id))

        system_content = bot.system_prompt or "You are a helpful AI assistant."
        knowledge = ""
        if bot.knowledge_base_config and bot.knowledge_base_config.get("text"):
            knowledge = f"\n\nContext information:\n{bot.knowledge_base_config['text']}"

        messages = [
            {"role": "system", "content": system_content + knowledge},
            {"role": "user", "content": body.message},
        ]

        import time
        start = time.perf_counter()
        response = await ai_service.complete(
            messages=messages,
            model=bot.model,
            temperature=bot.temperature,
        )
        latency = int((time.perf_counter() - start) * 1000)

        return BotTestResponse(
            reply=response["content"],
            latency_ms=latency,
            tokens_used=response.get("tokens_used", 0),
        )

    async def deploy(self, bot_id: uuid.UUID, user_id: uuid.UUID, body: BotDeployRequest) -> dict:
        bot = await self.db.get(Bot, bot_id)
        if not bot or bot.user_id != user_id:
            raise NotFoundError("Bot", str(bot_id))

        channels = {}
        for ch in body.channels:
            channels[ch] = {"enabled": True, "config": {}}
        bot.channels = channels
        bot.is_active = True
        bot.deployment_url = f"https://bots.omniai.app/{bot_id}"
        await self.db.flush()

        return {
            "bot_id": str(bot.id),
            "deployment_url": bot.deployment_url,
            "channels": bot.channels,
        }

    async def test_stream(self, bot_id: uuid.UUID, user_id: uuid.UUID, body) -> AsyncGenerator[str, None]:
        bot = await self.db.get(Bot, bot_id)
        if not bot or bot.user_id != user_id:
            raise NotFoundError("Bot", str(bot_id))

        system_content = bot.system_prompt or "You are a helpful AI assistant."
        knowledge = ""
        if bot.knowledge_base_config and bot.knowledge_base_config.get("text"):
            knowledge = f"\n\nContext information:\n{bot.knowledge_base_config['text']}"

        messages = [
            {"role": "system", "content": system_content + knowledge},
            {"role": "user", "content": body.message},
        ]

        stream = ai_service.complete_stream(
            messages=messages,
            model=bot.model,
            temperature=bot.temperature,
        )
        async for token in stream:
            yield token

    async def get_embed_code(self, bot_id: uuid.UUID, user_id: uuid.UUID, body) -> dict:
        bot = await self.db.get(Bot, bot_id)
        if not bot or bot.user_id != user_id:
            raise NotFoundError("Bot", str(bot_id))

        theme = body.theme or {}
        primary = theme.get("primary", "#2563EB")
        position = theme.get("position", "right")
        greeting = theme.get("greeting", "Hello! How can I help?")

        widget_config = {
            "bot_id": str(bot.id),
            "primary_color": primary,
            "position": position,
            "greeting": greeting,
        }
        bot.widget_config = widget_config
        await self.db.flush()

        embed_code = f"""<!-- OmniAI Chat Widget -->
<script>
(function() {{
    var botId = "{bot.id}";
    var primary = "{primary}";
    var position = "{position}";
    var greeting = "{greeting}";

    var container = document.createElement('div');
    container.id = 'omniai-chat-widget';
    container.innerHTML = `
        <div id="omniai-chat-btn" style="position:fixed;bottom:20px;${position}:20px;z-index:999999;width:60px;height:60px;border-radius:50%;background:${primary};color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:transform 0.2s;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div id="omniai-chat-box" style="display:none;position:fixed;bottom:90px;${position}:20px;z-index:999999;width:360px;height:500px;border-radius:16px;background:#fff;box-shadow:0 8px 40px rgba(0,0,0,0.15);overflow:hidden;font-family:system-ui,-apple-system,sans-serif;">
            <div style="background:${primary};color:#fff;padding:16px;font-weight:600;font-size:14px;">{greeting}</div>
            <div id="omniai-messages" style="height:360px;overflow-y:auto;padding:12px;font-size:13px;"></div>
            <div style="display:flex;border-top:1px solid #e2e8f0;padding:8px;">
                <input id="omniai-input" type="text" placeholder="Type a message..." style="flex:1;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;">
                <button id="omniai-send" style="margin-left:8px;background:${primary};color:#fff;border:none;border-radius:8px;padding:8px 16px;cursor:pointer;font-size:13px;">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(container);

    var btn = document.getElementById('omniai-chat-btn');
    var box = document.getElementById('omniai-chat-box');
    var input = document.getElementById('omniai-input');
    var send = document.getElementById('omniai-send');
    var messages = document.getElementById('omniai-messages');

    btn.onclick = function() {{
        box.style.display = box.style.display === 'none' ? 'block' : 'none';
    }};

    function addMessage(role, text) {{
        var div = document.createElement('div');
        div.style.cssText = 'margin-bottom:8px;text-align:' + (role === 'user' ? 'right' : 'left');
        var bubble = document.createElement('div');
        bubble.style.cssText = 'display:inline-block;padding:8px 12px;border-radius:12px;max-width:80%;font-size:13px;line-height:1.4;' +
            (role === 'user' ? 'background:' + primary + ';color:#fff;' : 'background:#f1f5f9;color:#111;');
        bubble.textContent = text;
        div.appendChild(bubble);
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }}

    function sendMessage() {{
        var text = input.value.trim();
        if (!text) return;
        addMessage('user', text);
        input.value = '';
        fetch('https://bots.omniai.app/api/messages', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{bot_id: botId, message: text}})
        }})
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{ addMessage('bot', data.reply); }})
        .catch(function() {{ addMessage('bot', 'Sorry, something went wrong.'); }});
    }}

    send.onclick = sendMessage;
    input.onkeypress = function(e) {{ if (e.key === 'Enter') sendMessage(); }};
}})();
</script>
<!-- End OmniAI Chat Widget -->"""

        widget_url = f"https://bots.omniai.app/embed/{bot.id}"

        return {
            "embed_code": embed_code,
            "widget_url": widget_url,
            "config": widget_config,
        }

    async def create_conversation(self, bot_id: uuid.UUID, session_id: str, channel: str, user_identifier: str | None = None) -> BotConversation:
        conv = BotConversation(
            bot_id=bot_id,
            session_id=session_id,
            channel=channel,
            user_identifier=user_identifier,
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def add_message(self, conversation_id: uuid.UUID, role: str, content: str, tokens_used: int = 0, latency_ms: int = 0) -> BotMessage:
        msg = BotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg
