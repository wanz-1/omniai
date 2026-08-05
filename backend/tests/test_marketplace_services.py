"""Service-layer tests for the marketplace stack.

Covers product publishing/purchasing, reviews with rating aggregation,
creator profiles and dashboards, plugin registry, AI verification flows
(including JSON fallbacks), and SDK generation.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.marketplace_extended import (
    CreatorProfile,
    ProductAnalytic,
)
from app.services.marketplace_creator import MarketplaceCreatorService
from app.services.marketplace_plugin import MarketplacePluginService
from app.services.marketplace_product import MarketplaceProductService
from app.services.marketplace_review import MarketplaceReviewService
from app.services.marketplace_sdk import MarketplaceSDKService
from app.services.marketplace_verification import MarketplaceVerificationService


def _mock_complete(content: str):
    return patch(
        "app.services.ai_service.ai_service.complete",
        AsyncMock(return_value={"content": content, "tokens_used": 0}),
    )


def _author(db, user_id=None):
    user_id = user_id or uuid.uuid4()
    db.add(CreatorProfile(user_id=user_id, display_name="Maker", total_sales=0,
                          total_revenue=0.0, average_rating=None))
    return user_id


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCT SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_categories(stateful_client):
    _client, db = stateful_client
    svc = MarketplaceProductService(db)
    cat = await svc.create_category("AI Agents", "ai-agents", "Agents", icon="bot")
    assert cat.slug == "ai-agents"
    assert len(await svc.list_categories()) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_product_creates_version(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)

    item = await svc.publish_product(author, {
        "name": "Sentiment Agent", "item_type": "agent", "category": "ai-agents",
        "description": "Analyzes sentiment", "tags": ["nlp"], "price": 19.99,
    })
    assert item.slug.startswith("sentiment-agent-")
    assert item.price == 19.99
    assert item.status == "draft"

    versions = await svc.get_product_versions(item.id)
    assert len(versions) == 1
    assert versions[0].version == "1.0.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_product_updates_creator_count(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    await svc.publish_product(author, {"name": "One", "item_type": "agent"})
    profile = await MarketplaceCreatorService(db).get_or_create_profile(author)
    assert profile.total_products == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_products_filters_and_search(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)

    for name, item_type, category in (
        ("Alpha Bot", "agent", "bots"),
        ("Beta Tracker", "tool", "bots"),
        ("Gamma Vision", "agent", "vision"),
    ):
        item = await svc.publish_product(author, {"name": name, "item_type": item_type, "category": category})
        item.status = "approved"
        item.downloads = 5

    assert len(await svc.list_products()) == 3
    assert len(await svc.list_products(category="bots")) == 2
    assert len(await svc.list_products(item_type="agent")) == 2
    assert len(await svc.list_products(search="alpha")) == 1
    # status filter hides drafts
    await svc.publish_product(author, {"name": "Drafty", "item_type": "agent"})
    assert len(await svc.list_products()) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_and_record_download(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "X", "item_type": "agent"})

    assert (await svc.get_product(item.id)).id == item.id
    assert await svc.get_product(uuid.uuid4()) is None

    await svc.record_download(item.id)
    assert item.downloads == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_version_updates_item(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "X", "item_type": "agent"})

    v = await svc.create_version(item.id, "2.1.0", "Fixed bugs")
    assert v.version == "2.1.0"
    assert v.changelog == "Fixed bugs"
    assert item.version == "2.1.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_purchase_product_flow(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "Paid", "item_type": "agent", "price": 25.0})

    buyer = uuid.uuid4()
    purchase = await svc.purchase_product(item.id, buyer, org_id=uuid.uuid4())
    assert purchase.amount == 25.0

    profile = await MarketplaceCreatorService(db).get_or_create_profile(author)
    assert profile.total_sales == 1
    assert profile.total_revenue == 25.0

    with pytest.raises(ValueError, match="Product not found"):
        await svc.purchase_product(uuid.uuid4(), buyer)

    # second purchase adds another sale
    await svc.purchase_product(item.id, uuid.uuid4())
    assert (await MarketplaceCreatorService(db).get_or_create_profile(author)).total_sales == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enterprise_listing_visibility(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "Enterprise", "item_type": "workflow"})

    listing = await svc.get_enterprise_listing(item.id, uuid.uuid4())
    assert listing is None

    from app.models.marketplace_extended import EnterpriseListing
    allowed = uuid.uuid4()
    listing = EnterpriseListing(product_id=item.id, is_private=True, allowed_orgs=[allowed])
    db.add(listing)

    assert await svc.get_enterprise_listing(item.id, allowed) is listing
    assert await svc.get_enterprise_listing(item.id, uuid.uuid4()) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_sdk_via_ai(stateful_client):
    _client, db = stateful_client
    with _mock_complete("class Client:"):
        sdk = await MarketplaceProductService(db).generate_sdk("python", ["auth"])
    assert sdk == "class Client:"


# ═══════════════════════════════════════════════════════════════════════════
# REVIEW SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_updates_ratings(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "Rated", "item_type": "agent"})

    reviews = MarketplaceReviewService(db)
    review = await reviews.create_review(item.id, uuid.uuid4(), rating=4, title="Good", content="works", pros=["fast"])
    assert review.rating == 4
    assert review.pros == ["fast"]

    await reviews.create_review(item.id, uuid.uuid4(), rating=2)
    assert item.rating == 3.0
    assert item.rating_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_listing_and_unapproved_hidden(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "R", "item_type": "agent"})

    reviews = MarketplaceReviewService(db)
    user = uuid.uuid4()
    await reviews.create_review(item.id, user, rating=5, content="great")

    assert len(await reviews.get_product_reviews(item.id)) == 1
    assert len(await reviews.get_user_reviews(user)) == 1
    assert len(await reviews.get_user_reviews(uuid.uuid4())) == 0

    hidden = await reviews.create_review(item.id, uuid.uuid4(), rating=1)
    hidden.is_approved = False
    assert len(await reviews.get_product_reviews(item.id)) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_creator_rating_update(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(author, {"name": "C", "item_type": "agent"})

    reviews = MarketplaceReviewService(db)
    await reviews.create_review(item.id, uuid.uuid4(), rating=5)
    profile = await MarketplaceCreatorService(db).get_or_create_profile(author)
    assert profile.average_rating == 5.0


# ═══════════════════════════════════════════════════════════════════════════
# CREATOR SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_or_create_and_update_profile(stateful_client):
    _client, db = stateful_client
    svc = MarketplaceCreatorService(db)
    user = uuid.uuid4()

    created = await svc.get_or_create_profile(user, display_name="Newbie")
    assert created.display_name == "Newbie"
    assert await svc.get_or_create_profile(user) is created

    updated = await svc.update_profile(user, display_name="Pro", bio="building")
    assert updated.display_name == "Pro"
    assert updated.bio == "building"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_creator_dashboard(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    prod = MarketplaceProductService(db)
    item = await prod.publish_product(author, {"name": "Dash", "item_type": "agent", "price": 10.0})
    item.status = "approved"

    buyer = uuid.uuid4()
    await prod.purchase_product(item.id, buyer)
    db.add(ProductAnalytic(product_id=item.id, date=datetime.now(timezone.utc),
                           views=100, installs=2, revenue=20.0))

    svc = MarketplaceCreatorService(db)
    dashboard = await svc.get_dashboard(author)
    assert dashboard["total_products"] == 1
    assert dashboard["total_sales"] == 1
    assert dashboard["total_revenue"] == 10.0
    assert dashboard["recent_sales"][0]["amount"] == 10.0
    assert dashboard["analytics"]["views_last_30d"] == 100
    assert dashboard["analytics"]["installs_last_30d"] == 3
    assert dashboard["analytics"]["revenue_last_30d"] == 30.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_creator_dashboard_empty(stateful_client):
    _client, db = stateful_client
    svc = MarketplaceCreatorService(db)
    dashboard = await svc.get_dashboard(uuid.uuid4())
    assert dashboard["total_products"] == 0
    assert dashboard["analytics"] == {"views_last_30d": 0, "installs_last_30d": 0, "revenue_last_30d": 0.0}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_creator_analytics_excludes_old_rows(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    prod = MarketplaceProductService(db)
    item = await prod.publish_product(author, {"name": "A", "item_type": "agent"})

    db.add(ProductAnalytic(product_id=item.id, date=datetime.now(timezone.utc) - timedelta(days=60),
                           views=500, installs=1, revenue=5.0))

    svc = MarketplaceCreatorService(db)
    dashboard = await svc.get_dashboard(author)
    assert dashboard["analytics"]["views_last_30d"] == 0

    stats = await svc.get_analytics(item.id)
    assert stats["totals"]["views"] == 500


# ═══════════════════════════════════════════════════════════════════════════
# PLUGIN SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_lifecycle(stateful_client):
    _client, db = stateful_client
    svc = MarketplacePluginService(db)
    author = uuid.uuid4()

    plugin = await svc.register_plugin("Slack Sync", "slack-sync", "integration",
                                       author, description="Syncs Slack", permissions=["read:slack"])
    assert plugin.plugin_type == "integration"
    assert plugin.permissions_required == ["read:slack"]
    assert plugin.is_active is True

    user = uuid.uuid4()
    inst = await svc.install_plugin(plugin.id, user, org_id=uuid.uuid4(), config={"channel": "#dev"})
    assert inst.installed_version == plugin.version
    assert inst.config == {"channel": "#dev"}

    with pytest.raises(ValueError, match="Plugin not found"):
        await svc.install_plugin(uuid.uuid4(), user)
    with pytest.raises(ValueError, match="already installed"):
        await svc.install_plugin(plugin.id, user)

    assert len(await svc.get_user_plugins(user)) == 1
    assert len(await svc.list_plugins("integration")) == 1

    updated = await svc.update_plugin_config(inst.id, {"channel": "#ops"})
    assert updated.config == {"channel": "#ops"}

    await svc.uninstall_plugin(inst.id)
    assert len(await svc.get_user_plugins(user)) == 0
    await svc.uninstall_plugin(inst.id)  # idempotent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_plugins_filters_type_and_active(stateful_client):
    _client, db = stateful_client
    svc = MarketplacePluginService(db)
    await svc.register_plugin("A", "a", "workflow", uuid.uuid4())
    p2 = await svc.register_plugin("B", "b", "integration", uuid.uuid4())
    p2.is_active = False

    names = {p.slug for p in await svc.list_plugins()}
    assert names == {"a"}
    assert {p.slug for p in await svc.list_plugins("integration")} == set()
    assert {p.slug for p in await svc.list_plugins("workflow")} == {"a"}


# ═══════════════════════════════════════════════════════════════════════════
# VERIFICATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_community_approves_above_threshold(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    item = await MarketplaceProductService(db).publish_product(
        author, {"name": "Verified", "item_type": "agent", "category": "nlp", "tags": ["ai"]})
    item.status = "draft"

    payload = {"overall_score": 80, "security_score": 90, "performance_score": 70,
               "quality_score": 85, "documentation_score": 75,
               "issues": [], "recommendations": ["docs"]}
    with _mock_complete(json.dumps(payload)):
        result = await MarketplaceVerificationService(db).verify_product(item.id, level="community")

    assert result.status == "completed"
    assert result.score == 80
    assert result.security_score == 90
    assert result.issues == []
    assert item.status == "approved"
    assert json.loads(result.report)["overall_score"] == 80


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_enterprise_rejects_low_score(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    item = await MarketplaceProductService(db).publish_product(
        author, {"name": "Sketchy", "item_type": "agent"})

    with _mock_complete(json.dumps({"overall_score": 40})):
        result = await MarketplaceVerificationService(db).verify_product(item.id, level="enterprise")

    assert result.status == "completed"
    assert result.score == 40
    assert item.status == "rejected"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_json_fallback_and_history(stateful_client):
    _client, db = stateful_client
    author = _author(db)
    item = await MarketplaceProductService(db).publish_product(
        author, {"name": "B", "item_type": "agent"})

    with _mock_complete("no json here"):
        result = await MarketplaceVerificationService(db).verify_product(item.id)
    assert result.score == 70
    assert result.issues == []
    assert item.status == "approved"  # 70 >= 60 community threshold

    history = await MarketplaceVerificationService(db).get_verification_history(item.id)
    assert len(history) == 1

    with pytest.raises(ValueError, match="Product not found"):
        await MarketplaceVerificationService(db).verify_product(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# SDK SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_sdk_template_only_for_small_feature_sets(stateful_client):
    _client, db = stateful_client
    svc = MarketplaceSDKService()

    result = await svc.generate_sdk("python", ["agents", "chat"])
    assert result["features"] == ["agents", "chat"]
    assert result["code"]  # template, not AI

    with _mock_complete("class ComprehensiveSDK:"):
        full = await svc.generate_sdk("typescript", ["a", "b", "c", "d", "e"])
    assert full["code"] == "class ComprehensiveSDK:"

    template = await svc.get_sdk_template("java")
    assert template["language"] == "java"
    assert template["code"]
