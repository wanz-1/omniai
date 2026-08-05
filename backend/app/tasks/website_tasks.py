import uuid

from app.tasks.celery_app import celery_app
from app.tasks.session import run, session_cm


@celery_app.task(bind=True, max_retries=3)
def build_website(self, website_id: str):
    async def _build():
        from app.core.constants import DeploymentStatus
        from app.models.website import Website

        async with session_cm() as db:
            website = await db.get(Website, uuid.UUID(website_id))
            if website is None:
                raise RuntimeError(f"Website {website_id} not found")

            website.deployment_status = DeploymentStatus.DEPLOYED
            website.preview_url = f"https://preview.omniai.app/{website_id}"
            website.generated_code_path = f"/generated/websites/{website_id}/"
            await db.commit()

            return {
                "status": "built",
                "website_id": website_id,
                "preview_url": website.preview_url,
            }

    try:
        return run(_build())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def deploy_website_task(self, website_id: str, platform: str):
    async def _deploy():
        from app.core.constants import DeploymentStatus
        from app.models.website import Website, WebsiteDeployment

        async with session_cm() as db:
            website = await db.get(Website, uuid.UUID(website_id))
            if website is None:
                raise RuntimeError(f"Website {website_id} not found")

            url = f"https://{website_id}.{platform}.omniai.app"
            deployment = WebsiteDeployment(
                website_id=website.id,
                platform=platform,
                status="deployed",
                url=url,
            )
            db.add(deployment)
            website.is_published = True
            website.published_url = url
            website.deployment_status = DeploymentStatus.DEPLOYED
            await db.commit()

            return {
                "status": "deployed",
                "website_id": website_id,
                "platform": platform,
                "url": url,
            }

    try:
        return run(_deploy())
    except Exception as exc:
        raise self.retry(exc=exc)
