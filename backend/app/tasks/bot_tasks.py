import datetime
import uuid

from app.tasks.celery_app import celery_app
from app.tasks.session import run, session_cm


@celery_app.task(bind=True, max_retries=3)
def train_bot_knowledge_base(self, bot_id: str):
    async def _train():
        from app.models.bot import Bot

        async with session_cm() as db:
            bot = await db.get(Bot, uuid.UUID(bot_id))
            if bot is None:
                raise RuntimeError(f"Bot {bot_id} not found")

            config = dict(bot.knowledge_base_config or {})
            files = list(config.get("files") or [])
            urls = list(config.get("urls") or [])
            text = config.get("text") or ""
            config["status"] = "trained"
            config["trained_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            config["source_count"] = len(files) + len(urls) + (1 if text else 0)
            config["character_count"] = (
                sum(len(str(f)) for f in files)
                + sum(len(str(u)) for u in urls)
                + len(str(text))
            )
            bot.knowledge_base_config = config
            await db.commit()

            return {
                "status": "training_completed",
                "bot_id": bot_id,
                "source_count": config["source_count"],
                "trained_at": config["trained_at"],
            }

    try:
        return run(_train())
    except Exception as exc:
        raise self.retry(exc=exc)
