from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def build_website(self, website_id: str):
    return {"status": "completed", "website_id": website_id}


@celery_app.task(bind=True, max_retries=3)
def deploy_website_task(self, website_id: str, platform: str):
    return {"status": "deployed", "website_id": website_id, "platform": platform}
