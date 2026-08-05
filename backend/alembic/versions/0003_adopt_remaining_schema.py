"""
Adopt the remaining schema under Alembic ownership (DB-001).

Generated baseline from the ORM metadata (227 total tables):
  - 0002 already owns 7 sprint-managed tables
  - this migration adopts the remaining 220 that were previously
    created at startup via Base.metadata.create_all.

Idempotent: CREATE TABLE/INDEX/VIEW IF NOT EXISTS semantics let it run
against both fresh databases and databases that already have the
schema from create_all. Existing deployments adopt in place; fresh
deployments get the complete schema from `alembic upgrade head`.

Regenerate with the script that produced this file if the metadata changes.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Named enum types (created idempotently for existing databases).
    if is_postgres:
        op.execute(sa.text("""
        DO $$
        BEGIN
            CREATE TYPE credittransactiontype AS ENUM ('PURCHASE', 'USAGE', 'REFUND', 'BONUS', 'TRANSFER');
            CREATE TYPE deploymentstatus AS ENUM ('DRAFT', 'BUILDING', 'DEPLOYED', 'FAILED');
            CREATE TYPE documenttype AS ENUM ('TXT', 'MARKDOWN', 'DOCX', 'PDF', 'RTF');
            CREATE TYPE mediatype AS ENUM ('IMAGE', 'AUDIO', 'VIDEO', 'DOCUMENT');
            CREATE TYPE notificationcategory AS ENUM ('DOCUMENT', 'WEBSITE', 'BOT', 'SYSTEM', 'BILLING', 'TEAM', 'GENERAL');
            CREATE TYPE notificationtype AS ENUM ('INFO', 'SUCCESS', 'WARNING', 'ERROR');
            CREATE TYPE organizationplan AS ENUM ('FREE', 'PRO', 'BUSINESS', 'ENTERPRISE');
            CREATE TYPE projecttype AS ENUM ('DOCUMENT', 'WEBSITE', 'BOT', 'CODE', 'GENERAL');
            CREATE TYPE role AS ENUM ('ADMIN', 'OWNER', 'MEMBER', 'USER');
            CREATE TYPE tone AS ENUM ('ACADEMIC', 'PROFESSIONAL', 'CASUAL', 'FORMAL', 'FRIENDLY', 'PERSUASIVE', 'INSTRUCTIVE', 'NARRATIVE', 'TECHNICAL', 'SIMPLE');
            CREATE TYPE videojobstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
            CREATE TYPE voicesessionstatus AS ENUM ('ACTIVE', 'PAUSED', 'ENDED', 'FAILED');
            CREATE TYPE websiteframework AS ENUM ('HTML_CSS', 'REACT', 'NEXTJS', 'VUE', 'ANGULAR', 'SVELTE');
            CREATE TYPE websitestyling AS ENUM ('TAILWIND', 'BOOTSTRAP', 'PLAIN_CSS');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """))

    # ai_communications
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_communications (
    	user_id UUID NOT NULL, 
    	communication_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	recipient VARCHAR(300), 
    	context TEXT, 
    	tone VARCHAR(20), 
    	generated_content TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	ai_suggestions JSONB, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # ai_meeting_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_meeting_sessions (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	participants JSONB, 
    	duration_minutes INTEGER, 
    	status VARCHAR(20) NOT NULL, 
    	transcript TEXT, 
    	summary TEXT, 
    	decisions JSONB, 
    	action_items JSONB, 
    	key_topics JSONB, 
    	recording_url VARCHAR(500), 
    	scheduled_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # ai_model_registry
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_model_registry (
    	name VARCHAR(200) NOT NULL, 
    	provider VARCHAR(50) NOT NULL, 
    	model_id VARCHAR(200) NOT NULL, 
    	model_type VARCHAR(50) NOT NULL, 
    	capabilities JSONB, 
    	cost_per_token FLOAT NOT NULL, 
    	latency_p50 FLOAT NOT NULL, 
    	latency_p99 FLOAT NOT NULL, 
    	max_tokens INTEGER NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	routing_rules JSONB, 
    	supported_regions JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # ai_organization_os
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_organization_os (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	metrics JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # app_categories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_categories (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	icon VARCHAR(200), 
    	display_order INTEGER NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug)
    )
    """))

    # backup_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS backup_records (
    	name VARCHAR(200) NOT NULL, 
    	backup_type VARCHAR(50) NOT NULL, 
    	target VARCHAR(200) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	size_bytes INTEGER, 
    	location TEXT, 
    	checksum VARCHAR(64), 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	error_message TEXT, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # connector_definitions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_definitions (
    	name VARCHAR(255) NOT NULL, 
    	connector_type VARCHAR(50) NOT NULL, 
    	category VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	icon_url VARCHAR(500), 
    	version VARCHAR(20) NOT NULL, 
    	auth_type VARCHAR(30) NOT NULL, 
    	config_schema JSONB NOT NULL, 
    	permissions JSONB NOT NULL, 
    	actions JSONB NOT NULL, 
    	events JSONB NOT NULL, 
    	is_official BOOLEAN NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	documentation_url VARCHAR(500), 
    	publisher VARCHAR(255), 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # design_assets
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS design_assets (
    	user_id UUID NOT NULL, 
    	name VARCHAR(300) NOT NULL, 
    	asset_type VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	style VARCHAR(100), 
    	prompt TEXT, 
    	generated_content TEXT, 
    	meta_data JSONB, 
    	is_favorite BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # developer_api_keys
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS developer_api_keys (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	key_prefix VARCHAR(10) NOT NULL, 
    	key_hash VARCHAR(128) NOT NULL, 
    	scopes JSONB, 
    	rate_limit INTEGER NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	last_used_at TIMESTAMP WITH TIME ZONE, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # evaluation_cases
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS evaluation_cases (
    	id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	category VARCHAR(100) NOT NULL, 
    	input TEXT NOT NULL, 
    	expected_behavior TEXT NOT NULL, 
    	evaluation_rules JSON, 
    	difficulty VARCHAR(20) NOT NULL, 
    	tags JSON, 
    	is_active BOOLEAN NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # executive_assistants
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS executive_assistants (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	role VARCHAR(50) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	capabilities JSONB, 
    	system_prompt TEXT, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	insights JSONB, 
    	recommendations JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # industries
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industries (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	icon VARCHAR(50), 
    	color VARCHAR(20), 
    	is_active BOOLEAN NOT NULL, 
    	sort_order INTEGER NOT NULL, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug)
    )
    """))

    # infrastructure_regions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS infrastructure_regions (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	provider VARCHAR(50) NOT NULL, 
    	location VARCHAR(200), 
    	status VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	priority INTEGER NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug)
    )
    """))

    # learning_paths
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS learning_paths (
    	user_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	subject VARCHAR(200), 
    	skill_level VARCHAR(20) NOT NULL, 
    	goals JSONB, 
    	modules JSONB, 
    	progress FLOAT NOT NULL, 
    	estimated_hours INTEGER, 
    	status VARCHAR(20) NOT NULL, 
    	resources JSONB, 
    	certificates JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # model_metrics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS model_metrics (
    	id UUID NOT NULL, 
    	model VARCHAR(100) NOT NULL, 
    	provider VARCHAR(50) NOT NULL, 
    	total_requests INTEGER NOT NULL, 
    	successful_requests INTEGER NOT NULL, 
    	failed_requests INTEGER NOT NULL, 
    	total_tokens INTEGER NOT NULL, 
    	prompt_tokens INTEGER NOT NULL, 
    	completion_tokens INTEGER NOT NULL, 
    	total_cost FLOAT NOT NULL, 
    	avg_latency_ms FLOAT, 
    	p95_latency_ms FLOAT, 
    	avg_quality_score FLOAT, 
    	period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    	period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # organization_policies
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS organization_policies (
    	organization_id UUID NOT NULL, 
    	policy_type VARCHAR(100) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	rules JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	auto_remediate BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # organizations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS organizations (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(100) NOT NULL, 
    	logo_url TEXT, 
    	plan organizationplan NOT NULL, 
    	settings JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # personal_ai_assistants
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS personal_ai_assistants (
    	user_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	role VARCHAR(100) NOT NULL, 
    	personality VARCHAR(50), 
    	system_prompt TEXT, 
    	capabilities JSONB, 
    	preferences JSONB, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	last_interaction TIMESTAMP WITH TIME ZONE, 
    	total_interactions INTEGER NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # physical_devices
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS physical_devices (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	name VARCHAR(200) NOT NULL, 
    	device_type VARCHAR(50) NOT NULL, 
    	protocol VARCHAR(50) NOT NULL, 
    	endpoint VARCHAR(500), 
    	credentials JSONB, 
    	config JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	last_seen TIMESTAMP WITH TIME ZONE, 
    	capabilities JSONB, 
    	metrics JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # product_categories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS product_categories (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	icon VARCHAR(50), 
    	parent_id UUID, 
    	sort_order INTEGER NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug), 
    	FOREIGN KEY(parent_id) REFERENCES product_categories (id)
    )
    """))

    # product_ideas
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS product_ideas (
    	user_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	industry VARCHAR(100), 
    	target_market TEXT, 
    	problem_statement TEXT, 
    	validation JSONB, 
    	market_research JSONB, 
    	user_stories JSONB, 
    	feature_roadmap JSONB, 
    	competitive_analysis JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # quality_scores
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS quality_scores (
    	id UUID NOT NULL, 
    	model VARCHAR(100) NOT NULL, 
    	period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    	period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    	overall_score FLOAT NOT NULL, 
    	accuracy_score FLOAT NOT NULL, 
    	safety_score FLOAT NOT NULL, 
    	citation_score FLOAT, 
    	latency_score FLOAT NOT NULL, 
    	cost_efficiency_score FLOAT, 
    	total_evaluations INTEGER NOT NULL, 
    	hallucination_rate FLOAT NOT NULL, 
    	avg_latency_ms INTEGER, 
    	total_tokens INTEGER, 
    	total_cost FLOAT, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # sdk_releases_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS sdk_releases_v4 (
    	sdk_name VARCHAR(100) NOT NULL, 
    	sdk_language VARCHAR(30) NOT NULL, 
    	sdk_version VARCHAR(20) NOT NULL, 
    	release_notes TEXT, 
    	documentation_url VARCHAR(500), 
    	download_url VARCHAR(500), 
    	is_latest BOOLEAN NOT NULL, 
    	published_at TIMESTAMP WITH TIME ZONE, 
    	breaking_changes JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # security_events
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS security_events (
    	event_type VARCHAR(100) NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	source VARCHAR(200), 
    	description TEXT, 
    	details JSONB, 
    	ip_address VARCHAR(50), 
    	user_id UUID, 
    	organization_id UUID, 
    	is_resolved BOOLEAN NOT NULL, 
    	resolved_at TIMESTAMP WITH TIME ZONE, 
    	action_taken TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # startup_projects
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS startup_projects (
    	user_id UUID NOT NULL, 
    	name VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	industry VARCHAR(100), 
    	status VARCHAR(20) NOT NULL, 
    	business_plan JSONB, 
    	market_research JSONB, 
    	brand_identity JSONB, 
    	technical_specs JSONB, 
    	generated_assets JSONB, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # users
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS users (
    	email VARCHAR(255) NOT NULL, 
    	password_hash VARCHAR(255), 
    	display_name VARCHAR(100) NOT NULL, 
    	avatar_url TEXT, 
    	bio TEXT, 
    	is_active BOOLEAN NOT NULL, 
    	is_verified BOOLEAN NOT NULL, 
    	is_superuser BOOLEAN NOT NULL, 
    	role role NOT NULL, 
    	two_factor_enabled BOOLEAN NOT NULL, 
    	two_factor_secret VARCHAR(64), 
    	preferences JSONB, 
    	last_login_at TIMESTAMP WITH TIME ZONE, 
    	last_ip VARCHAR(45), 
    	failed_attempts INTEGER NOT NULL, 
    	locked_until TIMESTAMP WITH TIME ZONE, 
    	last_failed_login TIMESTAMP WITH TIME ZONE, 
    	credits_balance INTEGER NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id)
    )
    """))

    # workflow_templates_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS workflow_templates_v4 (
    	publisher_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	category VARCHAR(100), 
    	industry VARCHAR(100), 
    	steps JSONB, 
    	ai_agents JSONB, 
    	forms JSONB, 
    	approval_rules JSONB, 
    	reports JSONB, 
    	dashboards JSONB, 
    	tags JSONB, 
    	is_verified BOOLEAN NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	total_installs INTEGER NOT NULL, 
    	avg_rating FLOAT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug)
    )
    """))

    # adoption_metrics_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS adoption_metrics_v4 (
    	organization_id UUID NOT NULL, 
    	feature_name VARCHAR(200) NOT NULL, 
    	total_users INTEGER NOT NULL, 
    	active_users INTEGER NOT NULL, 
    	adoption_rate FLOAT NOT NULL, 
    	engagement_score FLOAT NOT NULL, 
    	period VARCHAR(20) NOT NULL, 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # agent_profiles
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_profiles (
    	name VARCHAR(200) NOT NULL, 
    	role VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	system_prompt TEXT, 
    	model VARCHAR(100) NOT NULL, 
    	temperature FLOAT NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	is_template BOOLEAN NOT NULL, 
    	template_category VARCHAR(100), 
    	icon VARCHAR(50), 
    	color VARCHAR(7), 
    	config JSONB, 
    	published BOOLEAN NOT NULL, 
    	marketplace_listed BOOLEAN NOT NULL, 
    	price FLOAT, 
    	download_count INTEGER NOT NULL, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # agent_teams
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_teams (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	purpose VARCHAR(300), 
    	is_active BOOLEAN NOT NULL, 
    	is_template BOOLEAN NOT NULL, 
    	icon VARCHAR(50), 
    	color VARCHAR(7), 
    	config JSONB, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # ai_app_definitions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_app_definitions (
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	natural_language_prompt TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	components JSONB, 
    	data_model JSONB, 
    	ai_actions JSONB, 
    	workflows JSONB, 
    	api_config JSONB, 
    	ui_config JSONB, 
    	version VARCHAR(20) NOT NULL, 
    	is_published BOOLEAN NOT NULL, 
    	published_url VARCHAR(500), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # ai_audit_events
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_audit_events (
    	organization_id UUID NOT NULL, 
    	event_type VARCHAR(100) NOT NULL, 
    	actor_type VARCHAR(20) NOT NULL, 
    	actor_id UUID NOT NULL, 
    	action VARCHAR(200) NOT NULL, 
    	resource_type VARCHAR(100) NOT NULL, 
    	resource_id UUID, 
    	details JSONB, 
    	severity VARCHAR(20) NOT NULL, 
    	ip_address VARCHAR(50), 
    	user_agent VARCHAR(500), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # ai_decisions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_decisions (
    	id UUID NOT NULL, 
    	user_id UUID, 
    	organization_id UUID, 
    	session_id VARCHAR(200), 
    	model VARCHAR(100) NOT NULL, 
    	prompt_version VARCHAR(50), 
    	input_text TEXT NOT NULL, 
    	output_text TEXT NOT NULL, 
    	sources JSON, 
    	tools_used JSON, 
    	risk_level VARCHAR(20) NOT NULL, 
    	requires_review BOOLEAN NOT NULL, 
    	review_status VARCHAR(20) NOT NULL, 
    	final_action VARCHAR(50) NOT NULL, 
    	meta_data JSON, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # ai_departments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_departments (
    	organization_os_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	department_type VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	capabilities JSONB, 
    	agents JSONB, 
    	metrics JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_os_id) REFERENCES ai_organization_os (id)
    )
    """))

    # ai_evaluations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_evaluations (
    	id UUID NOT NULL, 
    	case_id UUID, 
    	model VARCHAR(100) NOT NULL, 
    	prompt_version VARCHAR(50), 
    	input_text TEXT NOT NULL, 
    	output_text TEXT NOT NULL, 
    	accuracy_score FLOAT, 
    	safety_score FLOAT, 
    	citation_score FLOAT, 
    	latency_ms INTEGER, 
    	tokens_used INTEGER, 
    	cost_estimate FLOAT, 
    	issues JSON, 
    	passed BOOLEAN NOT NULL, 
    	evaluated_by UUID, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(case_id) REFERENCES evaluation_cases (id), 
    	FOREIGN KEY(evaluated_by) REFERENCES users (id)
    )
    """))

    # ai_generated_products
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_generated_products (
    	startup_id UUID NOT NULL, 
    	product_type VARCHAR(50) NOT NULL, 
    	name VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	platform VARCHAR(50), 
    	generated_code TEXT, 
    	generated_design JSONB, 
    	specifications JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(startup_id) REFERENCES startup_projects (id)
    )
    """))

    # ai_monitoring_events_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_monitoring_events_v4 (
    	organization_id UUID NOT NULL, 
    	tenant_id UUID NOT NULL, 
    	event_type VARCHAR(100) NOT NULL, 
    	model_id VARCHAR(200), 
    	model_provider VARCHAR(100), 
    	latency_ms FLOAT, 
    	cost FLOAT, 
    	tokens_input INTEGER, 
    	tokens_output INTEGER, 
    	status VARCHAR(20) NOT NULL, 
    	error_message TEXT, 
    	user_id UUID, 
    	session_id VARCHAR(200), 
    	meta_data JSONB, 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # ai_policies
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_policies (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	policy_type VARCHAR(50) NOT NULL, 
    	rules JSONB, 
    	scope JSONB, 
    	severity VARCHAR(20) NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # api_keys
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS api_keys (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	name VARCHAR(100) NOT NULL, 
    	key_prefix VARCHAR(10) NOT NULL, 
    	key_hash VARCHAR(255) NOT NULL, 
    	permissions JSONB, 
    	last_used_at TIMESTAMP WITH TIME ZONE, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # app_listings
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_listings (
    	category_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	short_description VARCHAR(300), 
    	publisher VARCHAR(200) NOT NULL, 
    	publisher_website TEXT, 
    	icon_url TEXT, 
    	screenshots JSONB, 
    	features JSONB, 
    	pricing_model VARCHAR(20) NOT NULL, 
    	price FLOAT NOT NULL, 
    	currency VARCHAR(3) NOT NULL, 
    	is_verified BOOLEAN NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	documentation_url TEXT, 
    	support_url TEXT, 
    	config_schema JSONB, 
    	total_installs INTEGER NOT NULL, 
    	avg_rating FLOAT, 
    	tags JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(category_id) REFERENCES app_categories (id), 
    	UNIQUE (slug)
    )
    """))

    # approval_histories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS approval_histories (
    	organization_id UUID NOT NULL, 
    	requester_id UUID NOT NULL, 
    	reviewer_id UUID, 
    	action_type VARCHAR(40) NOT NULL, 
    	target_type VARCHAR(50) NOT NULL, 
    	target_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	comment TEXT, 
    	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
    	id UUID NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # approval_requests
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS approval_requests (
    	organization_id UUID NOT NULL, 
    	request_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	requester_id UUID NOT NULL, 
    	approver_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	priority VARCHAR(10) NOT NULL, 
    	resource_type VARCHAR(50), 
    	resource_id UUID, 
    	payload JSONB, 
    	decision_notes TEXT, 
    	decided_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(requester_id) REFERENCES users (id), 
    	FOREIGN KEY(approver_id) REFERENCES users (id)
    )
    """))

    # audit_logs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS audit_logs (
    	organization_id UUID, 
    	user_id UUID, 
    	action VARCHAR(100) NOT NULL, 
    	resource_type VARCHAR(50) NOT NULL, 
    	resource_id UUID, 
    	changes JSONB, 
    	ip_address INET, 
    	user_agent TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # audit_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS audit_records (
    	organization_id UUID NOT NULL, 
    	audit_type VARCHAR(20) NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	description TEXT NOT NULL, 
    	scope JSONB NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	auditor VARCHAR(255), 
    	audit_date TIMESTAMP WITHOUT TIME ZONE, 
    	completed_date TIMESTAMP WITHOUT TIME ZONE, 
    	findings_summary JSONB NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # autonomous_research
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS autonomous_research (
    	title VARCHAR(300) NOT NULL, 
    	topic VARCHAR(300) NOT NULL, 
    	depth VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	sources JSONB, 
    	findings JSONB, 
    	summary TEXT, 
    	report TEXT, 
    	recommendations JSONB, 
    	search_queries JSONB, 
    	confidence FLOAT, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # autonomous_workflows
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS autonomous_workflows (
    	organization_os_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	workflow_type VARCHAR(50) NOT NULL, 
    	trigger VARCHAR(100), 
    	steps JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	is_automatic BOOLEAN NOT NULL, 
    	last_executed TIMESTAMP WITH TIME ZONE, 
    	execution_count INTEGER NOT NULL, 
    	config JSONB, 
    	metrics JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_os_id) REFERENCES ai_organization_os (id)
    )
    """))

    # business_alerts
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS business_alerts (
    	organization_id UUID NOT NULL, 
    	agent_type VARCHAR(50) NOT NULL, 
    	alert_type VARCHAR(50) NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	message TEXT, 
    	metric_key VARCHAR(100), 
    	current_value FLOAT, 
    	threshold_value FLOAT, 
    	is_resolved BOOLEAN NOT NULL, 
    	resolved_at TIMESTAMP WITH TIME ZONE, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # business_metrics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS business_metrics (
    	organization_id UUID NOT NULL, 
    	agent_type VARCHAR(50) NOT NULL, 
    	metric_key VARCHAR(100) NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	value FLOAT NOT NULL, 
    	currency VARCHAR(3), 
    	unit VARCHAR(50), 
    	period_start TIMESTAMP WITH TIME ZONE, 
    	period_end TIMESTAMP WITH TIME ZONE, 
    	source VARCHAR(100), 
    	tags JSONB, 
    	raw_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # business_reports
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS business_reports (
    	organization_id UUID NOT NULL, 
    	agent_type VARCHAR(50) NOT NULL, 
    	report_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content JSONB, 
    	summary TEXT, 
    	recommendations JSONB, 
    	data_sources JSONB, 
    	period_start TIMESTAMP WITH TIME ZONE, 
    	period_end TIMESTAMP WITH TIME ZONE, 
    	generated_by_agent UUID, 
    	status VARCHAR(20) NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # business_workflows
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS business_workflows (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	workflow_type VARCHAR(50) NOT NULL, 
    	trigger VARCHAR(50) NOT NULL, 
    	steps JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	last_run_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # chat_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS chat_sessions (
    	title VARCHAR(200) NOT NULL, 
    	model VARCHAR(100) NOT NULL, 
    	system_prompt TEXT, 
    	is_archived BOOLEAN NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # cluster_deployments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS cluster_deployments (
    	region_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	cluster_type VARCHAR(50) NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	node_count INTEGER NOT NULL, 
    	endpoints JSONB, 
    	config JSONB, 
    	health_status VARCHAR(20) NOT NULL, 
    	last_health_check TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(region_id) REFERENCES infrastructure_regions (id)
    )
    """))

    # collaboration_agents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS collaboration_agents (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	agent_type VARCHAR(30) NOT NULL, 
    	capabilities JSONB NOT NULL, 
    	config JSONB NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # collaboration_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS collaboration_sessions (
    	organization_id UUID NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	session_type VARCHAR(30) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	description TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	ended_at TIMESTAMP WITH TIME ZONE, 
    	created_by UUID NOT NULL, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # compliance_checks
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_checks (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	check_type VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	scope JSONB NOT NULL, 
    	results_summary JSONB NOT NULL, 
    	started_by UUID NOT NULL, 
    	started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    	completed_at TIMESTAMP WITHOUT TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # compliance_document_reviews
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_document_reviews (
    	organization_id UUID NOT NULL, 
    	document_id UUID, 
    	document_type VARCHAR(20) NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	content TEXT NOT NULL, 
    	review_status VARCHAR(20) NOT NULL, 
    	issues JSONB NOT NULL, 
    	score FLOAT, 
    	reviewed_by UUID, 
    	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # compliance_reports
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_reports (
    	report_type VARCHAR(100) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	organization_id UUID, 
    	region_id UUID, 
    	data JSONB, 
    	findings JSONB, 
    	recommendations JSONB, 
    	generated_at TIMESTAMP WITH TIME ZONE, 
    	reviewed_at TIMESTAMP WITH TIME ZONE, 
    	reviewed_by UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(region_id) REFERENCES infrastructure_regions (id)
    )
    """))

    # compliance_reports_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_reports_v5 (
    	organization_id UUID NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	report_type VARCHAR(20) NOT NULL, 
    	content JSONB NOT NULL, 
    	generated_by UUID NOT NULL, 
    	generated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    	period_start TIMESTAMP WITHOUT TIME ZONE, 
    	period_end TIMESTAMP WITHOUT TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # compliance_rules
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_rules (
    	industry_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	rule_type VARCHAR(50) NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	condition JSONB, 
    	action JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # connector_api_keys
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_api_keys (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	key_hash VARCHAR(255) NOT NULL, 
    	key_prefix VARCHAR(10) NOT NULL, 
    	scopes JSONB NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	last_used_at TIMESTAMP WITH TIME ZONE, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # connector_integrations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_integrations (
    	organization_id UUID NOT NULL, 
    	connector_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	config JSONB NOT NULL, 
    	settings JSONB NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	last_sync_at TIMESTAMP WITH TIME ZONE, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(connector_id) REFERENCES connector_definitions (id)
    )
    """))

    # copilot_configs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_configs (
    	organization_id UUID NOT NULL, 
    	industry VARCHAR(50) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	is_active BOOLEAN NOT NULL, 
    	knowledge_sources JSONB NOT NULL, 
    	available_tools JSONB NOT NULL, 
    	permissions JSONB NOT NULL, 
    	compliance_rules JSONB NOT NULL, 
    	created_by UUID NOT NULL, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # copilot_domain_rules
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_domain_rules (
    	organization_id UUID NOT NULL, 
    	industry VARCHAR(50) NOT NULL, 
    	rule_type VARCHAR(50) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	conditions JSONB, 
    	actions JSONB, 
    	severity VARCHAR(20) NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # cost_savings_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS cost_savings_v4 (
    	organization_id UUID NOT NULL, 
    	category VARCHAR(100) NOT NULL, 
    	description TEXT, 
    	amount_saved FLOAT NOT NULL, 
    	currency VARCHAR(10) NOT NULL, 
    	period VARCHAR(20) NOT NULL, 
    	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	methodology TEXT, 
    	verified BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # creator_profiles
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS creator_profiles (
    	display_name VARCHAR(200) NOT NULL, 
    	bio TEXT, 
    	avatar_url TEXT, 
    	website TEXT, 
    	company VARCHAR(200), 
    	is_verified BOOLEAN NOT NULL, 
    	total_sales INTEGER NOT NULL, 
    	total_revenue FLOAT NOT NULL, 
    	total_products INTEGER NOT NULL, 
    	average_rating FLOAT, 
    	skills JSONB, 
    	social_links JSONB, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # credit_transactions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS credit_transactions (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	amount INTEGER NOT NULL, 
    	balance_after INTEGER NOT NULL, 
    	type credittransactiontype NOT NULL, 
    	description VARCHAR(300), 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # custom_connector_endpoints
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS custom_connector_endpoints (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	api_type VARCHAR(20) NOT NULL, 
    	base_url VARCHAR(500) NOT NULL, 
    	auth_method VARCHAR(30) NOT NULL, 
    	headers JSONB NOT NULL, 
    	endpoints JSONB NOT NULL, 
    	rate_limit INTEGER, 
    	is_active BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # data_residency_configs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS data_residency_configs (
    	organization_id UUID NOT NULL, 
    	region_id UUID NOT NULL, 
    	data_type VARCHAR(100) NOT NULL, 
    	retention_days INTEGER NOT NULL, 
    	encryption_enabled BOOLEAN NOT NULL, 
    	encryption_key TEXT, 
    	allow_export BOOLEAN NOT NULL, 
    	allow_processing BOOLEAN NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(region_id) REFERENCES infrastructure_regions (id)
    )
    """))

    # device_schedules
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS device_schedules (
    	device_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	schedule_type VARCHAR(50) NOT NULL, 
    	cron_expression VARCHAR(100), 
    	action JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	last_run TIMESTAMP WITH TIME ZONE, 
    	next_run TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(device_id) REFERENCES physical_devices (id)
    )
    """))

    # device_telemetry
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS device_telemetry (
    	device_id UUID NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	metric_value FLOAT NOT NULL, 
    	unit VARCHAR(20), 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	tags JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(device_id) REFERENCES physical_devices (id)
    )
    """))

    # digital_twins
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS digital_twins (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	twin_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	last_synced_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # enterprise_analytics_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS enterprise_analytics_v4 (
    	organization_id UUID NOT NULL, 
    	metric_category VARCHAR(50) NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	metric_value FLOAT NOT NULL, 
    	unit VARCHAR(50), 
    	period VARCHAR(20) NOT NULL, 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	dimensions JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # enterprise_integrations_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS enterprise_integrations_v4 (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	integration_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	credentials JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	last_sync_at TIMESTAMP WITH TIME ZONE, 
    	sync_frequency INTEGER, 
    	is_active BOOLEAN NOT NULL, 
    	webhook_url VARCHAR(500), 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # financial_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS financial_records (
    	organization_id UUID NOT NULL, 
    	record_type VARCHAR(50) NOT NULL, 
    	category VARCHAR(100) NOT NULL, 
    	description TEXT, 
    	amount FLOAT NOT NULL, 
    	currency VARCHAR(3) NOT NULL, 
    	transaction_date TIMESTAMP WITH TIME ZONE, 
    	reference VARCHAR(200), 
    	project_id UUID, 
    	donor VARCHAR(200), 
    	grant_code VARCHAR(100), 
    	budget_line VARCHAR(200), 
    	approval_status VARCHAR(20) NOT NULL, 
    	approved_by UUID, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # industry_agents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_agents (
    	industry_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	agent_type VARCHAR(100) NOT NULL, 
    	description TEXT, 
    	capabilities JSONB, 
    	system_prompt TEXT, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # industry_analytics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_analytics (
    	industry_id UUID NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	metric_value FLOAT NOT NULL, 
    	metric_type VARCHAR(50) NOT NULL, 
    	period VARCHAR(20) NOT NULL, 
    	period_start TIMESTAMP WITH TIME ZONE, 
    	period_end TIMESTAMP WITH TIME ZONE, 
    	dimensions JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # industry_compliance_packs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_compliance_packs (
    	organization_id UUID, 
    	industry VARCHAR(20) NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	description TEXT NOT NULL, 
    	requirements JSONB NOT NULL, 
    	policies JSONB NOT NULL, 
    	checks JSONB NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL
    )
    """))

    # industry_knowledge_bases
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_knowledge_bases (
    	industry_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	category VARCHAR(100), 
    	tags JSONB, 
    	source VARCHAR(100), 
    	meta_data JSONB, 
    	embedding JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # industry_templates
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_templates (
    	industry_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	template_type VARCHAR(100) NOT NULL, 
    	description TEXT, 
    	content JSONB, 
    	variables JSONB, 
    	category VARCHAR(100), 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # industry_workflows
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS industry_workflows (
    	industry_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	workflow_type VARCHAR(50) NOT NULL, 
    	steps JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	trigger VARCHAR(100), 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id)
    )
    """))

    # knowledge_connectors
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_connectors (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	connector_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	credentials JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	last_sync_at TIMESTAMP WITH TIME ZONE, 
    	sync_frequency INTEGER, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # knowledge_connectors_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_connectors_v5 (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	connector_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	credentials JSONB, 
    	auth_status VARCHAR(20) NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	last_sync_at TIMESTAMP WITH TIME ZONE, 
    	sync_interval_minutes INTEGER, 
    	total_documents INTEGER NOT NULL, 
    	webhook_url VARCHAR(500), 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # knowledge_documents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_documents (
    	organization_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	doc_type VARCHAR(50), 
    	source VARCHAR(100), 
    	source_url TEXT, 
    	tags JSONB, 
    	embedding_id VARCHAR(100), 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # knowledge_graph_nodes
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    	organization_id UUID NOT NULL, 
    	node_type VARCHAR(50) NOT NULL, 
    	external_id VARCHAR(500), 
    	name VARCHAR(500) NOT NULL, 
    	properties JSONB, 
    	embedding JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # marketplace_connectors
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS marketplace_connectors (
    	connector_id UUID NOT NULL, 
    	publisher_org_id UUID, 
    	is_verified BOOLEAN NOT NULL, 
    	rating FLOAT NOT NULL, 
    	download_count INTEGER NOT NULL, 
    	reviews JSONB NOT NULL, 
    	pricing_tier VARCHAR(20) NOT NULL, 
    	price FLOAT, 
    	documentation TEXT, 
    	support_url VARCHAR(500), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(connector_id) REFERENCES connector_definitions (id), 
    	FOREIGN KEY(publisher_org_id) REFERENCES organizations (id)
    )
    """))

    # media_assets
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS media_assets (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	asset_type mediatype NOT NULL, 
    	mime_type VARCHAR(100), 
    	storage_key VARCHAR(500) NOT NULL, 
    	size_bytes INTEGER, 
    	width INTEGER, 
    	height INTEGER, 
    	duration_ms INTEGER, 
    	thumbnail_key VARCHAR(500), 
    	ocr_text TEXT, 
    	ai_tags JSONB, 
    	ai_analysis JSONB, 
    	embedding_id VARCHAR(100), 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # model_registry_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS model_registry_v4 (
    	organization_id UUID NOT NULL, 
    	model_name VARCHAR(200) NOT NULL, 
    	model_provider VARCHAR(30) NOT NULL, 
    	model_version VARCHAR(30) NOT NULL, 
    	capabilities JSONB, 
    	cost_per_input_token FLOAT, 
    	cost_per_output_token FLOAT, 
    	latency_p50_ms FLOAT, 
    	latency_p99_ms FLOAT, 
    	is_active BOOLEAN NOT NULL, 
    	fallback_priority INTEGER, 
    	is_default BOOLEAN NOT NULL, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # multimodal_conversations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS multimodal_conversations (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	title VARCHAR(200), 
    	modality VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # notifications
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS notifications (
    	user_id UUID NOT NULL, 
    	type notificationtype NOT NULL, 
    	category notificationcategory NOT NULL, 
    	title VARCHAR(200) NOT NULL, 
    	body TEXT, 
    	link TEXT, 
    	is_read BOOLEAN NOT NULL, 
    	read_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # oauth_accounts
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS oauth_accounts (
    	user_id UUID NOT NULL, 
    	provider VARCHAR(50) NOT NULL, 
    	provider_user_id VARCHAR(255) NOT NULL, 
    	access_token TEXT, 
    	refresh_token TEXT, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # observability_dashboards
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS observability_dashboards (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	dashboard_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	metrics JSONB, 
    	is_default BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # organization_members
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS organization_members (
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	role role NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	CONSTRAINT uq_org_member UNIQUE (organization_id, user_id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # personal_knowledge_items
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS personal_knowledge_items (
    	assistant_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	source_type VARCHAR(50) NOT NULL, 
    	source_id VARCHAR(200), 
    	category VARCHAR(100), 
    	tags JSONB, 
    	summary TEXT, 
    	embedding JSONB, 
    	is_favorite BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(assistant_id) REFERENCES personal_ai_assistants (id)
    )
    """))

    # personal_memories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS personal_memories (
    	assistant_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	memory_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(300), 
    	content TEXT, 
    	summary TEXT, 
    	source VARCHAR(100), 
    	importance INTEGER NOT NULL, 
    	tags JSONB, 
    	meta_data JSONB, 
    	embedding JSONB, 
    	is_archived BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(assistant_id) REFERENCES personal_ai_assistants (id)
    )
    """))

    # personal_tasks
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS personal_tasks (
    	assistant_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	priority VARCHAR(10) NOT NULL, 
    	due_date TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	category VARCHAR(100), 
    	tags JSONB, 
    	result TEXT, 
    	ai_generated BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(assistant_id) REFERENCES personal_ai_assistants (id)
    )
    """))

    # plugin_definitions_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS plugin_definitions_v4 (
    	publisher_id UUID, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	plugin_type VARCHAR(30) NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	config_schema JSONB, 
    	hooks JSONB, 
    	permissions JSONB, 
    	is_verified BOOLEAN NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	download_count INTEGER NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(publisher_id) REFERENCES users (id)
    )
    """))

    # policies
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS policies (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(255) NOT NULL, 
    	policy_type VARCHAR(50) NOT NULL, 
    	description TEXT NOT NULL, 
    	content TEXT NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	version INTEGER NOT NULL, 
    	compliance_score FLOAT, 
    	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
    	reviewed_by UUID, 
    	effective_date TIMESTAMP WITHOUT TIME ZONE, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # projects
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS projects (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	type projecttype NOT NULL, 
    	meta_data JSONB, 
    	is_archived BOOLEAN NOT NULL, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # prompt_registry
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS prompt_registry (
    	id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	category VARCHAR(100) NOT NULL, 
    	owner UUID, 
    	current_version INTEGER NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	meta_data JSON, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(owner) REFERENCES users (id)
    )
    """))

    # regulations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS regulations (
    	organization_id UUID, 
    	name VARCHAR(255) NOT NULL, 
    	jurisdiction VARCHAR(255) NOT NULL, 
    	category VARCHAR(50) NOT NULL, 
    	description TEXT NOT NULL, 
    	requirements JSONB NOT NULL, 
    	effective_date TIMESTAMP WITHOUT TIME ZONE, 
    	expiration_date TIMESTAMP WITHOUT TIME ZONE, 
    	is_active BOOLEAN NOT NULL, 
    	source_url VARCHAR(500), 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL
    )
    """))

    # risk_scores
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS risk_scores (
    	organization_id UUID NOT NULL, 
    	score_type VARCHAR(20) NOT NULL, 
    	score FLOAT NOT NULL, 
    	max_score FLOAT NOT NULL, 
    	category VARCHAR(255), 
    	details JSONB, 
    	assessed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    	assessed_by UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # search_queries_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS search_queries_v5 (
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	query_text TEXT NOT NULL, 
    	filters JSONB, 
    	result_count INTEGER, 
    	execution_time_ms FLOAT, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # security_events_v6
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS security_events_v6 (
    	id UUID NOT NULL, 
    	user_id UUID, 
    	organization_id UUID, 
    	event_type VARCHAR(100) NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	ip_address VARCHAR(45), 
    	user_agent VARCHAR(500), 
    	action VARCHAR(200) NOT NULL, 
    	resource_type VARCHAR(100), 
    	resource_id VARCHAR(100), 
    	result VARCHAR(20) NOT NULL, 
    	detail TEXT, 
    	meta_data JSON, 
    	event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL
    )
    """))

    # simulation_models
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulation_models (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	model_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	is_template BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # solution_packages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS solution_packages (
    	industry_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	version VARCHAR(20) NOT NULL, 
    	is_installed BOOLEAN NOT NULL, 
    	installed_at TIMESTAMP WITH TIME ZONE, 
    	config JSONB, 
    	capabilities JSONB, 
    	agent_ids JSONB, 
    	workflow_ids JSONB, 
    	template_ids JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(industry_id) REFERENCES industries (id), 
    	UNIQUE (slug)
    )
    """))

    # studio_projects
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS studio_projects (
    	name VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	project_type VARCHAR(50) NOT NULL, 
    	frontend_framework VARCHAR(50), 
    	backend_framework VARCHAR(50), 
    	database_type VARCHAR(50), 
    	language VARCHAR(50) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	source VARCHAR(20) NOT NULL, 
    	file_tree JSONB, 
    	config JSONB, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # tenant_environments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS tenant_environments (
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	environment_type VARCHAR(50) NOT NULL, 
    	region VARCHAR(100) NOT NULL, 
    	config JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	is_ha BOOLEAN NOT NULL, 
    	scaling_policy JSONB, 
    	backup_config JSONB, 
    	dr_config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # usage_logs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS usage_logs (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	action VARCHAR(100) NOT NULL, 
    	resource_type VARCHAR(50), 
    	resource_id UUID, 
    	tokens_used INTEGER, 
    	credits_used INTEGER, 
    	duration_ms INTEGER, 
    	model VARCHAR(100), 
    	success BOOLEAN NOT NULL, 
    	error TEXT, 
    	ip_address VARCHAR(45), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # workflow_installations_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS workflow_installations_v4 (
    	template_id UUID NOT NULL, 
    	tenant_id UUID NOT NULL, 
    	organization_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	customizations JSONB, 
    	installed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	last_executed_at TIMESTAMP WITH TIME ZONE, 
    	execution_count INTEGER NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(template_id) REFERENCES workflow_templates_v4 (id)
    )
    """))

    # workflow_ratings_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS workflow_ratings_v4 (
    	template_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	rating INTEGER NOT NULL, 
    	review_text TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(template_id) REFERENCES workflow_templates_v4 (id)
    )
    """))

    # agent_analytics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_analytics (
    	total_tasks INTEGER NOT NULL, 
    	completed_tasks INTEGER NOT NULL, 
    	failed_tasks INTEGER NOT NULL, 
    	total_tokens INTEGER NOT NULL, 
    	avg_duration_ms FLOAT, 
    	avg_satisfaction FLOAT, 
    	top_skills JSONB, 
    	daily_usage JSONB, 
    	agent_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # agent_approval_requests
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_approval_requests (
    	organization_id UUID NOT NULL, 
    	agent_id UUID NOT NULL, 
    	agent_name VARCHAR(200) NOT NULL, 
    	requested_by UUID NOT NULL, 
    	capabilities JSONB, 
    	justification TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	reviewed_by UUID, 
    	review_notes TEXT, 
    	reviewed_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # agent_memories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_memories (
    	key VARCHAR(200) NOT NULL, 
    	content TEXT NOT NULL, 
    	memory_type VARCHAR(50) NOT NULL, 
    	category VARCHAR(100), 
    	importance INTEGER NOT NULL, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	is_organization BOOLEAN NOT NULL, 
    	agent_id UUID NOT NULL, 
    	user_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # agent_memory_network
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_memory_network (
    	key VARCHAR(200) NOT NULL, 
    	content TEXT NOT NULL, 
    	memory_type VARCHAR(50) NOT NULL, 
    	category VARCHAR(100), 
    	importance INTEGER NOT NULL, 
    	visibility VARCHAR(20) NOT NULL, 
    	source VARCHAR(100), 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	embedding JSONB, 
    	team_id UUID, 
    	organization_id UUID, 
    	agent_id UUID, 
    	user_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # agent_performance
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_performance (
    	total_tasks INTEGER NOT NULL, 
    	completed_tasks INTEGER NOT NULL, 
    	failed_tasks INTEGER NOT NULL, 
    	avg_score FLOAT, 
    	avg_response_time_ms FLOAT, 
    	total_tokens INTEGER NOT NULL, 
    	total_cost FLOAT NOT NULL, 
    	daily_metrics JSONB, 
    	review_scores JSONB, 
    	agent_id UUID NOT NULL, 
    	team_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id)
    )
    """))

    # agent_permissions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_permissions (
    	resource VARCHAR(100) NOT NULL, 
    	action VARCHAR(50) NOT NULL, 
    	access_level VARCHAR(20) NOT NULL, 
    	conditions JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	agent_id UUID NOT NULL, 
    	team_id UUID, 
    	granted_by UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id), 
    	FOREIGN KEY(granted_by) REFERENCES users (id)
    )
    """))

    # agent_session_links
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_session_links (
    	agent_id UUID NOT NULL, 
    	session_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES collaboration_agents (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # agent_skills
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_skills (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	category VARCHAR(100), 
    	proficiency INTEGER NOT NULL, 
    	agent_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # agent_task_delegations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_task_delegations (
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	priority INTEGER NOT NULL, 
    	progress FLOAT NOT NULL, 
    	deadline TIMESTAMP WITH TIME ZONE, 
    	input_data JSONB, 
    	output_data JSONB, 
    	result_summary TEXT, 
    	error TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	assignor_id UUID NOT NULL, 
    	assignee_id UUID NOT NULL, 
    	team_id UUID, 
    	parent_task_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(assignor_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(assignee_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id), 
    	FOREIGN KEY(parent_task_id) REFERENCES agent_task_delegations (id)
    )
    """))

    # agent_tasks
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_tasks (
    	title VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	priority INTEGER NOT NULL, 
    	progress FLOAT NOT NULL, 
    	result TEXT, 
    	error TEXT, 
    	input_data JSONB, 
    	output_data JSONB, 
    	execution_plan JSONB, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	agent_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	parent_task_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(parent_task_id) REFERENCES agent_tasks (id)
    )
    """))

    # agent_team_members
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_team_members (
    	role VARCHAR(100) NOT NULL, 
    	responsibilities TEXT, 
    	"order" INTEGER NOT NULL, 
    	is_lead BOOLEAN NOT NULL, 
    	team_id UUID NOT NULL, 
    	agent_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # agent_tools
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_tools (
    	name VARCHAR(200) NOT NULL, 
    	tool_type VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	config JSONB, 
    	enabled BOOLEAN NOT NULL, 
    	agent_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # ai_meeting_insights
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ai_meeting_insights (
    	session_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	summary TEXT, 
    	transcript_full TEXT, 
    	action_items JSONB NOT NULL, 
    	decisions JSONB NOT NULL, 
    	topics JSONB NOT NULL, 
    	sentiment VARCHAR(20), 
    	key_insights JSONB NOT NULL, 
    	participants_summary JSONB NOT NULL, 
    	generated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # app_components_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_components_v4 (
    	app_id UUID NOT NULL, 
    	component_type VARCHAR(30) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	config JSONB, 
    	position JSONB, 
    	is_visible BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(app_id) REFERENCES ai_app_definitions (id)
    )
    """))

    # app_installations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_installations (
    	app_id UUID NOT NULL, 
    	tenant_id UUID NOT NULL, 
    	organization_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	installed_version VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	customizations JSONB, 
    	installed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	last_used_at TIMESTAMP WITH TIME ZONE, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(app_id) REFERENCES app_listings (id)
    )
    """))

    # app_purchases
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_purchases (
    	app_id UUID NOT NULL, 
    	tenant_id UUID NOT NULL, 
    	organization_id UUID, 
    	purchase_type VARCHAR(20) NOT NULL, 
    	amount FLOAT NOT NULL, 
    	currency VARCHAR(3) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	license_key VARCHAR(200), 
    	purchased_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(app_id) REFERENCES app_listings (id)
    )
    """))

    # app_reviews_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS app_reviews_v4 (
    	app_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	rating INTEGER NOT NULL, 
    	review_text TEXT, 
    	is_verified_purchase BOOLEAN NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(app_id) REFERENCES app_listings (id)
    )
    """))

    # backup_records_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS backup_records_v4 (
    	tenant_id UUID NOT NULL, 
    	backup_type VARCHAR(50) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	size_bytes FLOAT NOT NULL, 
    	location TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(tenant_id) REFERENCES tenant_environments (id)
    )
    """))

    # bots
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS bots (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	system_prompt TEXT, 
    	model VARCHAR(100) NOT NULL, 
    	temperature FLOAT NOT NULL, 
    	industry VARCHAR(100), 
    	tone VARCHAR(50), 
    	knowledge_base_config JSONB, 
    	channels JSONB, 
    	webhook_secret VARCHAR(64), 
    	is_active BOOLEAN NOT NULL, 
    	deployment_url TEXT, 
    	widget_config JSONB, 
    	project_id UUID, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # build_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS build_records (
    	build_number INTEGER NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	trigger VARCHAR(20) NOT NULL, 
    	branch VARCHAR(100) NOT NULL, 
    	commit_message TEXT, 
    	log TEXT, 
    	errors TEXT, 
    	duration_ms INTEGER, 
    	output JSONB, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	project_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # business_workflow_executions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS business_workflow_executions (
    	workflow_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	current_step INTEGER, 
    	total_steps INTEGER, 
    	input_data JSONB, 
    	output_data JSONB, 
    	error TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(workflow_id) REFERENCES business_workflows (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # chat_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS chat_messages (
    	session_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	content TEXT NOT NULL, 
    	tokens_used INTEGER, 
    	latency_ms INTEGER, 
    	meta_data TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES chat_sessions (id)
    )
    """))

    # code_projects
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS code_projects (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	language VARCHAR(50) NOT NULL, 
    	framework VARCHAR(100), 
    	files JSONB, 
    	project_id UUID, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # collab_multimodal_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS collab_multimodal_messages (
    	session_id UUID NOT NULL, 
    	sender_id UUID NOT NULL, 
    	message_type VARCHAR(20) NOT NULL, 
    	content TEXT, 
    	media_url VARCHAR(1000), 
    	media_type VARCHAR(50), 
    	duration_seconds FLOAT, 
    	transcript TEXT, 
    	parent_id UUID, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # compliance_check_results
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS compliance_check_results (
    	check_id UUID NOT NULL, 
    	item_type VARCHAR(20) NOT NULL, 
    	item_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	finding TEXT, 
    	severity VARCHAR(20) NOT NULL, 
    	score FLOAT, 
    	details JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(check_id) REFERENCES compliance_checks (id) ON DELETE CASCADE
    )
    """))

    # connector_credentials
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_credentials (
    	integration_id UUID NOT NULL, 
    	credential_type VARCHAR(30) NOT NULL, 
    	encrypted_data JSONB NOT NULL, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	is_expired BOOLEAN NOT NULL, 
    	rotated_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES connector_integrations (id)
    )
    """))

    # connector_logs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_logs (
    	integration_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	level VARCHAR(10) NOT NULL, 
    	action VARCHAR(100) NOT NULL, 
    	message TEXT, 
    	details JSONB, 
    	ip_address VARCHAR(45), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES connector_integrations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # connector_permissions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS connector_permissions (
    	integration_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	principal_type VARCHAR(20) NOT NULL, 
    	principal_id UUID NOT NULL, 
    	permission VARCHAR(50) NOT NULL, 
    	granted_by UUID NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES connector_integrations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # copilot_analytics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_analytics (
    	organization_id UUID NOT NULL, 
    	copilot_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	event_type VARCHAR(50) NOT NULL, 
    	details JSONB, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(copilot_id) REFERENCES copilot_configs (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # copilot_knowledge_links
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_knowledge_links (
    	copilot_id UUID NOT NULL, 
    	document_id UUID, 
    	connector_id UUID, 
    	organization_id UUID NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(copilot_id) REFERENCES copilot_configs (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # copilot_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_sessions (
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	copilot_id UUID NOT NULL, 
    	title VARCHAR(200) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	context JSONB NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(copilot_id) REFERENCES copilot_configs (id)
    )
    """))

    # copilot_workflows
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_workflows (
    	organization_id UUID NOT NULL, 
    	copilot_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	workflow_type VARCHAR(50) NOT NULL, 
    	steps JSONB NOT NULL, 
    	triggers JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(copilot_id) REFERENCES copilot_configs (id)
    )
    """))

    # department_agents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS department_agents (
    	department_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	agent_type VARCHAR(100) NOT NULL, 
    	description TEXT, 
    	capabilities JSONB, 
    	system_prompt TEXT, 
    	config JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	performance JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(department_id) REFERENCES ai_departments (id)
    )
    """))

    # dev_projects
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS dev_projects (
    	name VARCHAR(300) NOT NULL, 
    	description TEXT, 
    	tech_stack JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	requirements JSONB, 
    	architecture JSONB, 
    	generated_code JSONB, 
    	test_results JSONB, 
    	security_review JSONB, 
    	deployment_config JSONB, 
    	repo_url TEXT, 
    	progress FLOAT NOT NULL, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	team_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id)
    )
    """))

    # digital_twin_entities
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS digital_twin_entities (
    	twin_id UUID NOT NULL, 
    	entity_type VARCHAR(50) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	attributes JSONB, 
    	relationships JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(twin_id) REFERENCES digital_twins (id)
    )
    """))

    # disaster_recovery_plans
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS disaster_recovery_plans (
    	tenant_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	rpo_minutes INTEGER NOT NULL, 
    	rto_minutes INTEGER NOT NULL, 
    	regions JSONB, 
    	steps JSONB, 
    	last_tested_at TIMESTAMP WITH TIME ZONE, 
    	status VARCHAR(20) NOT NULL, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(tenant_id) REFERENCES tenant_environments (id)
    )
    """))

    # document_collaborations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS document_collaborations (
    	session_id UUID NOT NULL, 
    	document_id UUID NOT NULL, 
    	document_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	content JSONB NOT NULL, 
    	version INTEGER NOT NULL, 
    	is_locked BOOLEAN NOT NULL, 
    	locked_by UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # documents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS documents (
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	humanized_content TEXT, 
    	content_type documenttype NOT NULL, 
    	tone tone, 
    	audience VARCHAR(100), 
    	readability_score FLOAT, 
    	original_ai_score FLOAT, 
    	humanized_ai_score FLOAT, 
    	word_count INTEGER, 
    	language VARCHAR(10) NOT NULL, 
    	file_path TEXT, 
    	file_size BIGINT, 
    	project_id UUID, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # enterprise_listings
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS enterprise_listings (
    	is_private BOOLEAN NOT NULL, 
    	allowed_orgs JSONB, 
    	license_type VARCHAR(50) NOT NULL, 
    	custom_price FLOAT, 
    	support_level VARCHAR(30) NOT NULL, 
    	sla_document TEXT, 
    	product_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # findings
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS findings (
    	audit_id UUID, 
    	organization_id UUID NOT NULL, 
    	finding_type VARCHAR(30) NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	description TEXT NOT NULL, 
    	severity VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	source VARCHAR(255), 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(audit_id) REFERENCES audit_records (id) ON DELETE CASCADE, 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # fine_tuned_models_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS fine_tuned_models_v4 (
    	base_model_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	training_data_config JSONB, 
    	hyperparameters JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	model_endpoint VARCHAR(500), 
    	accuracy FLOAT, 
    	cost_multiplier FLOAT, 
    	created_by UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(base_model_id) REFERENCES model_registry_v4 (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # hallucination_events
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS hallucination_events (
    	id UUID NOT NULL, 
    	evaluation_id UUID, 
    	claim TEXT NOT NULL, 
    	confidence FLOAT NOT NULL, 
    	evidence_found BOOLEAN NOT NULL, 
    	evidence_source VARCHAR(500), 
    	severity VARCHAR(20) NOT NULL, 
    	category VARCHAR(50) NOT NULL, 
    	detail TEXT, 
    	model VARCHAR(100) NOT NULL, 
    	detected_by VARCHAR(50) NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(evaluation_id) REFERENCES ai_evaluations (id)
    )
    """))

    # human_reviews
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS human_reviews (
    	id UUID NOT NULL, 
    	decision_id UUID, 
    	reviewer_id UUID NOT NULL, 
    	organization_id UUID, 
    	status VARCHAR(20) NOT NULL, 
    	risk_level VARCHAR(20) NOT NULL, 
    	input_summary TEXT, 
    	output_summary TEXT, 
    	decision VARCHAR(20), 
    	comments TEXT, 
    	reviewed_at TIMESTAMP WITH TIME ZONE, 
    	expires_at TIMESTAMP WITH TIME ZONE, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(decision_id) REFERENCES ai_decisions (id), 
    	FOREIGN KEY(reviewer_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # integration_auth_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS integration_auth_v4 (
    	integration_id UUID NOT NULL, 
    	auth_type VARCHAR(20) NOT NULL, 
    	access_token TEXT, 
    	refresh_token TEXT, 
    	token_expires_at TIMESTAMP WITH TIME ZONE, 
    	scopes JSONB, 
    	is_valid BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES enterprise_integrations_v4 (id)
    )
    """))

    # knowledge_documents_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_documents_v5 (
    	connector_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	external_id VARCHAR(500), 
    	title VARCHAR(500) NOT NULL, 
    	content TEXT, 
    	file_type VARCHAR(50), 
    	file_size INTEGER, 
    	url VARCHAR(1000), 
    	path VARCHAR(1000), 
    	author VARCHAR(200), 
    	created_by UUID NOT NULL, 
    	checksum VARCHAR(64), 
    	indexed_at TIMESTAMP WITH TIME ZONE, 
    	is_indexed BOOLEAN NOT NULL, 
    	is_deleted BOOLEAN NOT NULL, 
    	meta_data JSONB, 
    	embedding JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(connector_id) REFERENCES knowledge_connectors_v5 (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # knowledge_graph_edges
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    	source_node_id UUID NOT NULL, 
    	target_node_id UUID NOT NULL, 
    	edge_type VARCHAR(50) NOT NULL, 
    	properties JSONB, 
    	weight FLOAT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(source_node_id) REFERENCES knowledge_graph_nodes (id), 
    	FOREIGN KEY(target_node_id) REFERENCES knowledge_graph_nodes (id)
    )
    """))

    # knowledge_sources_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_sources_v4 (
    	connector_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	source_type VARCHAR(50) NOT NULL, 
    	source_path VARCHAR(500), 
    	total_documents INTEGER NOT NULL, 
    	last_indexed_at TIMESTAMP WITH TIME ZONE, 
    	status VARCHAR(20) NOT NULL, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(connector_id) REFERENCES knowledge_connectors (id)
    )
    """))

    # model_benchmarks_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS model_benchmarks_v4 (
    	model_id UUID NOT NULL, 
    	benchmark_name VARCHAR(100) NOT NULL, 
    	score FLOAT NOT NULL, 
    	metric_name VARCHAR(100) NOT NULL, 
    	tested_at TIMESTAMP WITH TIME ZONE, 
    	test_dataset VARCHAR(200), 
    	notes TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(model_id) REFERENCES model_registry_v4 (id)
    )
    """))

    # monitoring_metrics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS monitoring_metrics (
    	metric_name VARCHAR(200) NOT NULL, 
    	metric_value FLOAT NOT NULL, 
    	metric_type VARCHAR(50) NOT NULL, 
    	unit VARCHAR(20), 
    	source VARCHAR(100), 
    	region_id UUID, 
    	cluster_id UUID, 
    	tags JSONB, 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(region_id) REFERENCES infrastructure_regions (id), 
    	FOREIGN KEY(cluster_id) REFERENCES cluster_deployments (id)
    )
    """))

    # multimodal_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS multimodal_messages (
    	conversation_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	content JSONB, 
    	text TEXT, 
    	media_asset_ids JSONB, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(conversation_id) REFERENCES multimodal_conversations (id)
    )
    """))

    # ocr_results
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS ocr_results (
    	asset_id UUID NOT NULL, 
    	raw_text TEXT, 
    	structured_data JSONB, 
    	confidence FLOAT, 
    	pages JSONB, 
    	language VARCHAR(10), 
    	processing_time_ms INTEGER, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(asset_id) REFERENCES media_assets (id)
    )
    """))

    # plugin_definitions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS plugin_definitions (
    	name VARCHAR(200) NOT NULL, 
    	slug VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	plugin_type VARCHAR(50) NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	entry_point VARCHAR(300), 
    	config_schema JSONB, 
    	permissions_required JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	is_official BOOLEAN NOT NULL, 
    	source_url TEXT, 
    	documentation_url TEXT, 
    	author_id UUID NOT NULL, 
    	product_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	UNIQUE (slug), 
    	FOREIGN KEY(author_id) REFERENCES users (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id)
    )
    """))

    # product_analytics
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS product_analytics (
    	date TIMESTAMP WITH TIME ZONE NOT NULL, 
    	views INTEGER NOT NULL, 
    	unique_visitors INTEGER NOT NULL, 
    	installs INTEGER NOT NULL, 
    	revenue FLOAT NOT NULL, 
    	refunds INTEGER NOT NULL, 
    	product_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id)
    )
    """))

    # product_reviews
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS product_reviews (
    	rating INTEGER NOT NULL, 
    	title VARCHAR(300), 
    	content TEXT, 
    	pros JSONB, 
    	cons JSONB, 
    	is_verified_purchase BOOLEAN NOT NULL, 
    	is_approved BOOLEAN NOT NULL, 
    	product_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # product_versions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS product_versions (
    	version VARCHAR(20) NOT NULL, 
    	changelog TEXT, 
    	release_notes TEXT, 
    	file_url TEXT, 
    	file_size INTEGER NOT NULL, 
    	checksum VARCHAR(64), 
    	is_deprecated BOOLEAN NOT NULL, 
    	requires JSONB, 
    	compatibility JSONB, 
    	product_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id)
    )
    """))

    # prompt_versions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS prompt_versions (
    	id UUID NOT NULL, 
    	prompt_id UUID NOT NULL, 
    	version INTEGER NOT NULL, 
    	template TEXT NOT NULL, 
    	parameters JSON, 
    	model_target VARCHAR(100), 
    	change_notes TEXT, 
    	created_by UUID, 
    	status VARCHAR(20) NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(prompt_id) REFERENCES prompt_registry (id) ON DELETE CASCADE, 
    	FOREIGN KEY(created_by) REFERENCES users (id)
    )
    """))

    # published_apps_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS published_apps_v4 (
    	app_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	published_url VARCHAR(500), 
    	api_endpoint VARCHAR(500), 
    	deployed_version VARCHAR(20), 
    	deployed_at TIMESTAMP WITH TIME ZONE, 
    	status VARCHAR(20) NOT NULL, 
    	analytics JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(app_id) REFERENCES ai_app_definitions (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # regional_deployments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS regional_deployments (
    	tenant_id UUID NOT NULL, 
    	region VARCHAR(100) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	endpoint_url TEXT, 
    	deployed_at TIMESTAMP WITH TIME ZONE, 
    	health_status VARCHAR(20) NOT NULL, 
    	metrics JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(tenant_id) REFERENCES tenant_environments (id)
    )
    """))

    # regulatory_updates
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS regulatory_updates (
    	organization_id UUID, 
    	regulation_id UUID, 
    	title VARCHAR(255) NOT NULL, 
    	description TEXT NOT NULL, 
    	change_type VARCHAR(20) NOT NULL, 
    	impact VARCHAR(20) NOT NULL, 
    	affected_areas JSONB NOT NULL, 
    	recommended_actions TEXT, 
    	detected_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    	is_reviewed BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE SET NULL, 
    	FOREIGN KEY(regulation_id) REFERENCES regulations (id) ON DELETE SET NULL
    )
    """))

    # repositories
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS repositories (
    	name VARCHAR(300) NOT NULL, 
    	url TEXT, 
    	provider VARCHAR(20) NOT NULL, 
    	external_id VARCHAR(200), 
    	default_branch VARCHAR(100) NOT NULL, 
    	is_private BOOLEAN NOT NULL, 
    	clone_url TEXT, 
    	token TEXT, 
    	config JSONB, 
    	user_id UUID NOT NULL, 
    	project_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id)
    )
    """))

    # scenarios
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS scenarios (
    	organization_id UUID NOT NULL, 
    	twin_id UUID, 
    	model_id UUID, 
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	scenario_type VARCHAR(50) NOT NULL, 
    	base_state JSONB, 
    	variables JSONB, 
    	assumptions JSONB, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(twin_id) REFERENCES digital_twins (id), 
    	FOREIGN KEY(model_id) REFERENCES simulation_models (id)
    )
    """))

    # screen_share_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS screen_share_sessions (
    	session_id UUID NOT NULL, 
    	host_id UUID NOT NULL, 
    	stream_url VARCHAR(1000), 
    	is_active BOOLEAN NOT NULL, 
    	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	ended_at TIMESTAMP WITH TIME ZONE, 
    	recording_url VARCHAR(1000), 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # security_scans
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS security_scans (
    	scan_type VARCHAR(50) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	risk_score FLOAT, 
    	vulnerabilities JSONB, 
    	summary TEXT, 
    	recommendations JSONB, 
    	report TEXT, 
    	severity_counts JSONB, 
    	project_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # service_deployments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS service_deployments (
    	cluster_id UUID NOT NULL, 
    	service_name VARCHAR(200) NOT NULL, 
    	service_type VARCHAR(50) NOT NULL, 
    	version VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	replicas INTEGER NOT NULL, 
    	target_replicas INTEGER NOT NULL, 
    	resources JSONB, 
    	config JSONB, 
    	endpoints JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(cluster_id) REFERENCES cluster_deployments (id)
    )
    """))

    # session_participants
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS session_participants (
    	session_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	joined_at TIMESTAMP WITH TIME ZONE, 
    	left_at TIMESTAMP WITH TIME ZONE, 
    	is_present BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # session_recordings
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS session_recordings (
    	session_id UUID NOT NULL, 
    	recording_type VARCHAR(20) NOT NULL, 
    	file_url VARCHAR(1000), 
    	duration_seconds FLOAT, 
    	file_size INTEGER, 
    	status VARCHAR(20) NOT NULL, 
    	transcript TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	ended_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # studio_documentations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS studio_documentations (
    	doc_type VARCHAR(50) NOT NULL, 
    	title VARCHAR(300) NOT NULL, 
    	content TEXT, 
    	format VARCHAR(20) NOT NULL, 
    	sections JSONB, 
    	meta_data JSONB, 
    	project_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # studio_files
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS studio_files (
    	path VARCHAR(500) NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	content TEXT, 
    	language VARCHAR(50), 
    	size INTEGER NOT NULL, 
    	is_binary BOOLEAN NOT NULL, 
    	sha_hash VARCHAR(64), 
    	encoding VARCHAR(20), 
    	project_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id)
    )
    """))

    # sync_jobs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS sync_jobs (
    	integration_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	sync_type VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	items_total INTEGER NOT NULL, 
    	items_processed INTEGER NOT NULL, 
    	items_failed INTEGER NOT NULL, 
    	items_created INTEGER NOT NULL, 
    	items_updated INTEGER NOT NULL, 
    	items_deleted INTEGER NOT NULL, 
    	error_log JSONB NOT NULL, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES connector_integrations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # sync_records_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS sync_records_v4 (
    	integration_id UUID NOT NULL, 
    	sync_type VARCHAR(50) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	records_processed INTEGER NOT NULL, 
    	records_failed INTEGER NOT NULL, 
    	error_log JSONB, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(integration_id) REFERENCES enterprise_integrations_v4 (id)
    )
    """))

    # test_runs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS test_runs (
    	name VARCHAR(300) NOT NULL, 
    	test_type VARCHAR(30) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	framework VARCHAR(50), 
    	total_tests INTEGER NOT NULL, 
    	passed INTEGER NOT NULL, 
    	failed INTEGER NOT NULL, 
    	skipped INTEGER NOT NULL, 
    	coverage FLOAT, 
    	duration_ms INTEGER, 
    	log TEXT, 
    	results JSONB, 
    	project_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # usage_metrics_v4
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS usage_metrics_v4 (
    	tenant_id UUID NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	metric_value FLOAT NOT NULL, 
    	unit VARCHAR(20), 
    	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	dimensions JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(tenant_id) REFERENCES tenant_environments (id)
    )
    """))

    # user_feedback
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS user_feedback (
    	id UUID NOT NULL, 
    	user_id UUID, 
    	decision_id UUID, 
    	model VARCHAR(100) NOT NULL, 
    	rating INTEGER NOT NULL, 
    	rating_type VARCHAR(20) NOT NULL, 
    	correction TEXT, 
    	comment TEXT, 
    	category VARCHAR(100), 
    	tags JSON, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(decision_id) REFERENCES ai_decisions (id)
    )
    """))

    # verification_results
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS verification_results (
    	level VARCHAR(30) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	score FLOAT, 
    	security_score FLOAT, 
    	performance_score FLOAT, 
    	quality_score FLOAT, 
    	documentation_score FLOAT, 
    	issues JSONB, 
    	report TEXT, 
    	checked_at TIMESTAMP WITH TIME ZONE, 
    	product_id UUID NOT NULL, 
    	reviewer_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(product_id) REFERENCES marketplace_items (id), 
    	FOREIGN KEY(reviewer_id) REFERENCES users (id)
    )
    """))

    # video_jobs
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS video_jobs (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	input_asset_id UUID NOT NULL, 
    	job_type VARCHAR(50) NOT NULL, 
    	status videojobstatus NOT NULL, 
    	progress FLOAT NOT NULL, 
    	output JSONB, 
    	error TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(input_asset_id) REFERENCES media_assets (id)
    )
    """))

    # voice_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS voice_sessions (
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	agent_id UUID, 
    	status voicesessionstatus NOT NULL, 
    	duration_ms INTEGER, 
    	language VARCHAR(10) NOT NULL, 
    	transcription JSONB, 
    	recording_url TEXT, 
    	config JSONB, 
    	ended_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id)
    )
    """))

    # webhook_events
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS webhook_events (
    	organization_id UUID NOT NULL, 
    	integration_id UUID, 
    	event_type VARCHAR(100) NOT NULL, 
    	source VARCHAR(100) NOT NULL, 
    	payload JSONB NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	processed_at TIMESTAMP WITH TIME ZONE, 
    	error_message TEXT, 
    	retry_count INTEGER NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(integration_id) REFERENCES connector_integrations (id)
    )
    """))

    # websites
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS websites (
    	name VARCHAR(200) NOT NULL, 
    	template_id VARCHAR(100), 
    	framework websiteframework NOT NULL, 
    	styling websitestyling NOT NULL, 
    	pages JSONB, 
    	theme_config JSONB, 
    	generated_code_path TEXT, 
    	preview_url TEXT, 
    	published_url TEXT, 
    	deployment_status deploymentstatus NOT NULL, 
    	custom_domain VARCHAR(255), 
    	is_published BOOLEAN NOT NULL, 
    	project_id UUID, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(project_id) REFERENCES projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # whiteboard_sessions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS whiteboard_sessions (
    	session_id UUID NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	canvas_data JSONB NOT NULL, 
    	strokes JSONB NOT NULL, 
    	shapes JSONB NOT NULL, 
    	annotations JSONB NOT NULL, 
    	width INTEGER NOT NULL, 
    	height INTEGER NOT NULL, 
    	is_locked BOOLEAN NOT NULL, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES collaboration_sessions (id)
    )
    """))

    # workflows
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS workflows (
    	name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	is_active BOOLEAN NOT NULL, 
    	trigger_event VARCHAR(100), 
    	trigger_config JSONB, 
    	agent_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # agent_executions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_executions (
    	status VARCHAR(20) NOT NULL, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	duration_ms INTEGER, 
    	tokens_used INTEGER NOT NULL, 
    	steps_completed INTEGER NOT NULL, 
    	steps_total INTEGER NOT NULL, 
    	input TEXT, 
    	output TEXT, 
    	error TEXT, 
    	execution_log JSONB, 
    	agent_id UUID NOT NULL, 
    	task_id UUID, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(agent_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(task_id) REFERENCES agent_tasks (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # agent_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_messages (
    	content TEXT NOT NULL, 
    	message_type VARCHAR(50) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	meta_data JSONB, 
    	read_at TIMESTAMP WITH TIME ZONE, 
    	sender_id UUID NOT NULL, 
    	receiver_id UUID NOT NULL, 
    	task_id UUID, 
    	team_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(sender_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(receiver_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(task_id) REFERENCES agent_tasks (id), 
    	FOREIGN KEY(team_id) REFERENCES agent_teams (id)
    )
    """))

    # agent_reviews
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS agent_reviews (
    	score FLOAT NOT NULL, 
    	content TEXT, 
    	review_type VARCHAR(50) NOT NULL, 
    	criteria_scores JSONB, 
    	confidence FLOAT, 
    	suggestions JSONB, 
    	is_approved BOOLEAN NOT NULL, 
    	reviewer_id UUID NOT NULL, 
    	reviewee_id UUID NOT NULL, 
    	task_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(reviewer_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(reviewee_id) REFERENCES agent_profiles (id), 
    	FOREIGN KEY(task_id) REFERENCES agent_task_delegations (id)
    )
    """))

    # bot_conversations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS bot_conversations (
    	bot_id UUID NOT NULL, 
    	session_id VARCHAR(100) NOT NULL, 
    	channel VARCHAR(50) NOT NULL, 
    	user_identifier VARCHAR(255), 
    	meta_data JSONB, 
    	is_active BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(bot_id) REFERENCES bots (id)
    )
    """))

    # branch_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS branch_records (
    	name VARCHAR(200) NOT NULL, 
    	is_default BOOLEAN NOT NULL, 
    	is_protected BOOLEAN NOT NULL, 
    	head_commit_id VARCHAR(200), 
    	repository_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(repository_id) REFERENCES repositories (id)
    )
    """))

    # code_generations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS code_generations (
    	code_project_id UUID NOT NULL, 
    	prompt TEXT NOT NULL, 
    	generated_code TEXT NOT NULL, 
    	language VARCHAR(50) NOT NULL, 
    	tokens_used INTEGER, 
    	model VARCHAR(100) NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(code_project_id) REFERENCES code_projects (id)
    )
    """))

    # commit_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS commit_records (
    	external_id VARCHAR(200), 
    	message TEXT NOT NULL, 
    	author_name VARCHAR(200), 
    	author_email VARCHAR(200), 
    	branch VARCHAR(100) NOT NULL, 
    	files_changed JSONB, 
    	additions INTEGER NOT NULL, 
    	deletions INTEGER NOT NULL, 
    	is_ai_generated BOOLEAN NOT NULL, 
    	committed_at TIMESTAMP WITH TIME ZONE, 
    	repository_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(repository_id) REFERENCES repositories (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # copilot_approvals
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_approvals (
    	session_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	requester_id UUID NOT NULL, 
    	reviewer_id UUID, 
    	request_type VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	details JSONB, 
    	status VARCHAR(20) NOT NULL, 
    	reviewer_comment TEXT, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	resolved_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES copilot_sessions (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(requester_id) REFERENCES users (id), 
    	FOREIGN KEY(reviewer_id) REFERENCES users (id)
    )
    """))

    # copilot_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_messages (
    	session_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	content TEXT, 
    	tool_calls JSONB, 
    	tool_results JSONB, 
    	meta_data JSONB, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES copilot_sessions (id)
    )
    """))

    # copilot_recommendations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_recommendations (
    	session_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	industry VARCHAR(50) NOT NULL, 
    	recommendation_type VARCHAR(20) NOT NULL, 
    	title VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	confidence FLOAT, 
    	data JSONB, 
    	applied BOOLEAN NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES copilot_sessions (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # copilot_workflow_executions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS copilot_workflow_executions (
    	workflow_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	input_data JSONB, 
    	output_data JSONB, 
    	error TEXT, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(workflow_id) REFERENCES copilot_workflows (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # corrective_actions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS corrective_actions (
    	finding_id UUID, 
    	organization_id UUID NOT NULL, 
    	title VARCHAR(255) NOT NULL, 
    	description TEXT NOT NULL, 
    	action_plan TEXT NOT NULL, 
    	priority VARCHAR(20) NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	assigned_to UUID, 
    	deadline TIMESTAMP WITHOUT TIME ZONE, 
    	completed_at TIMESTAMP WITHOUT TIME ZONE, 
    	verification_notes TEXT, 
    	created_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(finding_id) REFERENCES findings (id) ON DELETE CASCADE, 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """))

    # document_versions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS document_versions (
    	document_id UUID NOT NULL, 
    	version_number INTEGER NOT NULL, 
    	content TEXT NOT NULL, 
    	change_summary VARCHAR(500), 
    	ai_score FLOAT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(document_id) REFERENCES documents (id)
    )
    """))

    # enterprise_documents
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS enterprise_documents (
    	source_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	title VARCHAR(500) NOT NULL, 
    	content TEXT, 
    	file_type VARCHAR(50), 
    	file_size INTEGER, 
    	url VARCHAR(1000), 
    	author VARCHAR(200), 
    	indexed_at TIMESTAMP WITH TIME ZONE, 
    	embedding JSONB, 
    	meta_data JSONB, 
    	is_indexed BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(source_id) REFERENCES knowledge_sources_v4 (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # knowledge_chunks_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_chunks_v5 (
    	document_id UUID NOT NULL, 
    	chunk_index INTEGER NOT NULL, 
    	content TEXT, 
    	embedding JSONB, 
    	token_count INTEGER, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(document_id) REFERENCES knowledge_documents_v5 (id)
    )
    """))

    # knowledge_permissions_v5
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS knowledge_permissions_v5 (
    	document_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	principal_type VARCHAR(20) NOT NULL, 
    	principal_id UUID NOT NULL, 
    	permission_level VARCHAR(20) NOT NULL, 
    	granted_by UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(document_id) REFERENCES knowledge_documents_v5 (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # plugin_installations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS plugin_installations (
    	config JSONB, 
    	is_enabled BOOLEAN NOT NULL, 
    	installed_version VARCHAR(20) NOT NULL, 
    	plugin_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	organization_id UUID, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(plugin_id) REFERENCES plugin_definitions (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # simulation_variables
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulation_variables (
    	scenario_id UUID NOT NULL, 
    	name VARCHAR(200) NOT NULL, 
    	variable_type VARCHAR(50) NOT NULL, 
    	current_value FLOAT NOT NULL, 
    	simulated_value FLOAT, 
    	unit VARCHAR(50) NOT NULL, 
    	min_range FLOAT, 
    	max_range FLOAT, 
    	description TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(scenario_id) REFERENCES scenarios (id)
    )
    """))

    # simulations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulations (
    	organization_id UUID NOT NULL, 
    	scenario_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	simulation_type VARCHAR(50) NOT NULL, 
    	input_snapshot JSONB, 
    	output_data JSONB, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	error TEXT, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(scenario_id) REFERENCES scenarios (id)
    )
    """))

    # studio_deployments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS studio_deployments (
    	deployment_number INTEGER NOT NULL, 
    	status VARCHAR(20) NOT NULL, 
    	target VARCHAR(50) NOT NULL, 
    	url TEXT, 
    	environment VARCHAR(20) NOT NULL, 
    	config JSONB, 
    	log TEXT, 
    	build_id UUID, 
    	started_at TIMESTAMP WITH TIME ZONE, 
    	completed_at TIMESTAMP WITH TIME ZONE, 
    	project_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(build_id) REFERENCES build_records (id), 
    	FOREIGN KEY(project_id) REFERENCES studio_projects (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id)
    )
    """))

    # voice_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS voice_messages (
    	session_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	text TEXT, 
    	audio_url TEXT, 
    	duration_ms INTEGER, 
    	confidence FLOAT, 
    	language VARCHAR(10), 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(session_id) REFERENCES voice_sessions (id)
    )
    """))

    # website_deployments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS website_deployments (
    	website_id UUID NOT NULL, 
    	platform VARCHAR(50) NOT NULL, 
    	status VARCHAR(50) NOT NULL, 
    	url TEXT, 
    	error_message TEXT, 
    	logs JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(website_id) REFERENCES websites (id)
    )
    """))

    # workflow_steps
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS workflow_steps (
    	name VARCHAR(200) NOT NULL, 
    	step_type VARCHAR(50) NOT NULL, 
    	config JSONB, 
    	"order" INTEGER NOT NULL, 
    	position_x FLOAT, 
    	position_y FLOAT, 
    	workflow_id UUID NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(workflow_id) REFERENCES workflows (id)
    )
    """))

    # bot_messages
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS bot_messages (
    	conversation_id UUID NOT NULL, 
    	role VARCHAR(20) NOT NULL, 
    	content TEXT NOT NULL, 
    	tokens_used INTEGER, 
    	latency_ms INTEGER, 
    	meta_data JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(conversation_id) REFERENCES bot_conversations (id)
    )
    """))

    # citation_records
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS citation_records (
    	organization_id UUID NOT NULL, 
    	user_id UUID NOT NULL, 
    	search_query_id UUID NOT NULL, 
    	document_id UUID NOT NULL, 
    	chunk_id UUID, 
    	relevance_score FLOAT, 
    	cited_text TEXT, 
    	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    	id UUID NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    	FOREIGN KEY(user_id) REFERENCES users (id), 
    	FOREIGN KEY(search_query_id) REFERENCES search_queries_v5 (id), 
    	FOREIGN KEY(document_id) REFERENCES knowledge_documents_v5 (id), 
    	FOREIGN KEY(chunk_id) REFERENCES knowledge_chunks_v5 (id)
    )
    """))

    # predictions
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS predictions (
    	simulation_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	prediction_type VARCHAR(50) NOT NULL, 
    	metric_name VARCHAR(200) NOT NULL, 
    	predicted_value FLOAT NOT NULL, 
    	confidence FLOAT NOT NULL, 
    	lower_bound FLOAT, 
    	upper_bound FLOAT, 
    	time_period VARCHAR(50) NOT NULL, 
    	details JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(simulation_id) REFERENCES simulations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # risk_assessments
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS risk_assessments (
    	simulation_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	category VARCHAR(50) NOT NULL, 
    	risk_name VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	probability FLOAT NOT NULL, 
    	impact FLOAT NOT NULL, 
    	risk_score FLOAT NOT NULL, 
    	mitigation TEXT, 
    	status VARCHAR(20) NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(simulation_id) REFERENCES simulations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # simulation_outcomes
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulation_outcomes (
    	simulation_id UUID NOT NULL, 
    	scenario_id UUID NOT NULL, 
    	outcome_type VARCHAR(50) NOT NULL, 
    	description TEXT, 
    	severity VARCHAR(20) NOT NULL, 
    	probability FLOAT NOT NULL, 
    	impact_value FLOAT, 
    	details JSONB, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(simulation_id) REFERENCES simulations (id), 
    	FOREIGN KEY(scenario_id) REFERENCES scenarios (id)
    )
    """))

    # simulation_recommendations
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulation_recommendations (
    	simulation_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	title VARCHAR(200) NOT NULL, 
    	description TEXT, 
    	recommendation_type VARCHAR(50) NOT NULL, 
    	expected_impact VARCHAR(50) NOT NULL, 
    	confidence FLOAT NOT NULL, 
    	alternatives JSONB, 
    	is_applied BOOLEAN NOT NULL, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(simulation_id) REFERENCES simulations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # simulation_reports
    op.execute(sa.text("""

    CREATE TABLE IF NOT EXISTS simulation_reports (
    	simulation_id UUID NOT NULL, 
    	organization_id UUID NOT NULL, 
    	title VARCHAR(200) NOT NULL, 
    	report_type VARCHAR(50) NOT NULL, 
    	content JSONB, 
    	generated_by UUID NOT NULL, 
    	generated_at TIMESTAMP WITH TIME ZONE, 
    	id UUID NOT NULL, 
    	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    	PRIMARY KEY (id), 
    	FOREIGN KEY(simulation_id) REFERENCES simulations (id), 
    	FOREIGN KEY(organization_id) REFERENCES organizations (id)
    )
    """))

    # Indexes (separate from the inline CREATE TABLE definitions).
    op.execute(sa.text("""
    CREATE INDEX IF NOT EXISTS ix_ai_communications_id ON ai_communications (id);
    CREATE INDEX IF NOT EXISTS ix_ai_communications_user_id ON ai_communications (user_id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_sessions_id ON ai_meeting_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_sessions_organization_id ON ai_meeting_sessions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_sessions_user_id ON ai_meeting_sessions (user_id);
    CREATE INDEX IF NOT EXISTS ix_ai_model_registry_id ON ai_model_registry (id);
    CREATE INDEX IF NOT EXISTS ix_ai_organization_os_id ON ai_organization_os (id);
    CREATE INDEX IF NOT EXISTS ix_ai_organization_os_organization_id ON ai_organization_os (organization_id);
    CREATE INDEX IF NOT EXISTS ix_app_categories_id ON app_categories (id);
    CREATE INDEX IF NOT EXISTS ix_backup_records_id ON backup_records (id);
    CREATE INDEX IF NOT EXISTS ix_connector_definitions_id ON connector_definitions (id);
    CREATE INDEX IF NOT EXISTS ix_design_assets_id ON design_assets (id);
    CREATE INDEX IF NOT EXISTS ix_design_assets_user_id ON design_assets (user_id);
    CREATE INDEX IF NOT EXISTS ix_developer_api_keys_id ON developer_api_keys (id);
    CREATE INDEX IF NOT EXISTS ix_developer_api_keys_organization_id ON developer_api_keys (organization_id);
    CREATE INDEX IF NOT EXISTS ix_evaluation_cases_category ON evaluation_cases (category);
    CREATE INDEX IF NOT EXISTS ix_executive_assistants_id ON executive_assistants (id);
    CREATE INDEX IF NOT EXISTS ix_executive_assistants_organization_id ON executive_assistants (organization_id);
    CREATE INDEX IF NOT EXISTS ix_executive_assistants_user_id ON executive_assistants (user_id);
    CREATE INDEX IF NOT EXISTS ix_industries_id ON industries (id);
    CREATE INDEX IF NOT EXISTS ix_infrastructure_regions_id ON infrastructure_regions (id);
    CREATE INDEX IF NOT EXISTS ix_learning_paths_id ON learning_paths (id);
    CREATE INDEX IF NOT EXISTS ix_learning_paths_user_id ON learning_paths (user_id);
    CREATE INDEX IF NOT EXISTS idx_model_metrics_model_period ON model_metrics (model, period_start);
    CREATE INDEX IF NOT EXISTS ix_model_metrics_model ON model_metrics (model);
    CREATE INDEX IF NOT EXISTS ix_organization_policies_id ON organization_policies (id);
    CREATE INDEX IF NOT EXISTS ix_organization_policies_organization_id ON organization_policies (organization_id);
    CREATE INDEX IF NOT EXISTS ix_organizations_id ON organizations (id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug);
    CREATE INDEX IF NOT EXISTS ix_personal_ai_assistants_id ON personal_ai_assistants (id);
    CREATE INDEX IF NOT EXISTS ix_personal_ai_assistants_user_id ON personal_ai_assistants (user_id);
    CREATE INDEX IF NOT EXISTS ix_physical_devices_id ON physical_devices (id);
    CREATE INDEX IF NOT EXISTS ix_physical_devices_organization_id ON physical_devices (organization_id);
    CREATE INDEX IF NOT EXISTS ix_physical_devices_user_id ON physical_devices (user_id);
    CREATE INDEX IF NOT EXISTS ix_product_categories_id ON product_categories (id);
    CREATE INDEX IF NOT EXISTS ix_product_categories_parent_id ON product_categories (parent_id);
    CREATE INDEX IF NOT EXISTS ix_product_ideas_id ON product_ideas (id);
    CREATE INDEX IF NOT EXISTS ix_product_ideas_user_id ON product_ideas (user_id);
    CREATE INDEX IF NOT EXISTS ix_sdk_releases_v4_id ON sdk_releases_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_security_events_event_type ON security_events (event_type);
    CREATE INDEX IF NOT EXISTS ix_security_events_id ON security_events (id);
    CREATE INDEX IF NOT EXISTS ix_security_events_organization_id ON security_events (organization_id);
    CREATE INDEX IF NOT EXISTS ix_security_events_user_id ON security_events (user_id);
    CREATE INDEX IF NOT EXISTS ix_startup_projects_id ON startup_projects (id);
    CREATE INDEX IF NOT EXISTS ix_startup_projects_user_id ON startup_projects (user_id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
    CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
    CREATE INDEX IF NOT EXISTS ix_workflow_templates_v4_category ON workflow_templates_v4 (category);
    CREATE INDEX IF NOT EXISTS ix_workflow_templates_v4_id ON workflow_templates_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_workflow_templates_v4_publisher_id ON workflow_templates_v4 (publisher_id);
    CREATE INDEX IF NOT EXISTS ix_adoption_metrics_v4_id ON adoption_metrics_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_adoption_metrics_v4_organization_id ON adoption_metrics_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_agent_profiles_id ON agent_profiles (id);
    CREATE INDEX IF NOT EXISTS ix_agent_profiles_organization_id ON agent_profiles (organization_id);
    CREATE INDEX IF NOT EXISTS ix_agent_profiles_user_id ON agent_profiles (user_id);
    CREATE INDEX IF NOT EXISTS ix_agent_teams_id ON agent_teams (id);
    CREATE INDEX IF NOT EXISTS ix_agent_teams_organization_id ON agent_teams (organization_id);
    CREATE INDEX IF NOT EXISTS ix_agent_teams_user_id ON agent_teams (user_id);
    CREATE INDEX IF NOT EXISTS ix_ai_app_definitions_id ON ai_app_definitions (id);
    CREATE INDEX IF NOT EXISTS ix_ai_app_definitions_organization_id ON ai_app_definitions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_ai_app_definitions_user_id ON ai_app_definitions (user_id);
    CREATE INDEX IF NOT EXISTS ix_ai_audit_events_actor_id ON ai_audit_events (actor_id);
    CREATE INDEX IF NOT EXISTS ix_ai_audit_events_id ON ai_audit_events (id);
    CREATE INDEX IF NOT EXISTS ix_ai_audit_events_organization_id ON ai_audit_events (organization_id);
    CREATE INDEX IF NOT EXISTS idx_ai_decisions_user ON ai_decisions (user_id, created_at);
    CREATE INDEX IF NOT EXISTS ix_ai_decisions_user_id ON ai_decisions (user_id);
    CREATE INDEX IF NOT EXISTS ix_ai_departments_id ON ai_departments (id);
    CREATE INDEX IF NOT EXISTS ix_ai_departments_organization_os_id ON ai_departments (organization_os_id);
    CREATE INDEX IF NOT EXISTS ix_ai_generated_products_id ON ai_generated_products (id);
    CREATE INDEX IF NOT EXISTS ix_ai_generated_products_startup_id ON ai_generated_products (startup_id);
    CREATE INDEX IF NOT EXISTS ix_ai_monitoring_events_v4_id ON ai_monitoring_events_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_ai_monitoring_events_v4_organization_id ON ai_monitoring_events_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_ai_monitoring_events_v4_tenant_id ON ai_monitoring_events_v4 (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_ai_policies_id ON ai_policies (id);
    CREATE INDEX IF NOT EXISTS ix_ai_policies_organization_id ON ai_policies (organization_id);
    CREATE INDEX IF NOT EXISTS ix_api_keys_id ON api_keys (id);
    CREATE INDEX IF NOT EXISTS ix_api_keys_organization_id ON api_keys (organization_id);
    CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys (user_id);
    CREATE INDEX IF NOT EXISTS ix_app_listings_category_id ON app_listings (category_id);
    CREATE INDEX IF NOT EXISTS ix_app_listings_id ON app_listings (id);
    CREATE INDEX IF NOT EXISTS ix_approval_histories_id ON approval_histories (id);
    CREATE INDEX IF NOT EXISTS ix_approval_requests_id ON approval_requests (id);
    CREATE INDEX IF NOT EXISTS ix_approval_requests_organization_id ON approval_requests (organization_id);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs (id);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_organization_id ON audit_logs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
    CREATE INDEX IF NOT EXISTS ix_audit_records_id ON audit_records (id);
    CREATE INDEX IF NOT EXISTS ix_autonomous_research_id ON autonomous_research (id);
    CREATE INDEX IF NOT EXISTS ix_autonomous_research_organization_id ON autonomous_research (organization_id);
    CREATE INDEX IF NOT EXISTS ix_autonomous_research_user_id ON autonomous_research (user_id);
    CREATE INDEX IF NOT EXISTS ix_autonomous_workflows_id ON autonomous_workflows (id);
    CREATE INDEX IF NOT EXISTS ix_autonomous_workflows_organization_os_id ON autonomous_workflows (organization_os_id);
    CREATE INDEX IF NOT EXISTS ix_business_alerts_id ON business_alerts (id);
    CREATE INDEX IF NOT EXISTS ix_business_alerts_organization_id ON business_alerts (organization_id);
    CREATE INDEX IF NOT EXISTS ix_business_metrics_agent_type ON business_metrics (agent_type);
    CREATE INDEX IF NOT EXISTS ix_business_metrics_id ON business_metrics (id);
    CREATE INDEX IF NOT EXISTS ix_business_metrics_organization_id ON business_metrics (organization_id);
    CREATE INDEX IF NOT EXISTS ix_business_reports_id ON business_reports (id);
    CREATE INDEX IF NOT EXISTS ix_business_reports_organization_id ON business_reports (organization_id);
    CREATE INDEX IF NOT EXISTS ix_business_workflows_id ON business_workflows (id);
    CREATE INDEX IF NOT EXISTS ix_business_workflows_organization_id ON business_workflows (organization_id);
    CREATE INDEX IF NOT EXISTS ix_chat_sessions_id ON chat_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id);
    CREATE INDEX IF NOT EXISTS ix_cluster_deployments_id ON cluster_deployments (id);
    CREATE INDEX IF NOT EXISTS ix_cluster_deployments_region_id ON cluster_deployments (region_id);
    CREATE INDEX IF NOT EXISTS ix_collaboration_agents_id ON collaboration_agents (id);
    CREATE INDEX IF NOT EXISTS ix_collaboration_agents_organization_id ON collaboration_agents (organization_id);
    CREATE INDEX IF NOT EXISTS ix_collaboration_sessions_id ON collaboration_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_collaboration_sessions_organization_id ON collaboration_sessions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_compliance_checks_id ON compliance_checks (id);
    CREATE INDEX IF NOT EXISTS ix_compliance_document_reviews_id ON compliance_document_reviews (id);
    CREATE INDEX IF NOT EXISTS ix_compliance_reports_id ON compliance_reports (id);
    CREATE INDEX IF NOT EXISTS ix_compliance_reports_organization_id ON compliance_reports (organization_id);
    CREATE INDEX IF NOT EXISTS ix_compliance_reports_region_id ON compliance_reports (region_id);
    CREATE INDEX IF NOT EXISTS ix_compliance_reports_v5_id ON compliance_reports_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_compliance_rules_id ON compliance_rules (id);
    CREATE INDEX IF NOT EXISTS ix_compliance_rules_industry_id ON compliance_rules (industry_id);
    CREATE INDEX IF NOT EXISTS ix_connector_api_keys_id ON connector_api_keys (id);
    CREATE INDEX IF NOT EXISTS ix_connector_api_keys_organization_id ON connector_api_keys (organization_id);
    CREATE INDEX IF NOT EXISTS ix_connector_integrations_id ON connector_integrations (id);
    CREATE INDEX IF NOT EXISTS ix_connector_integrations_organization_id ON connector_integrations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_configs_id ON copilot_configs (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_configs_organization_id ON copilot_configs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_domain_rules_id ON copilot_domain_rules (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_domain_rules_organization_id ON copilot_domain_rules (organization_id);
    CREATE INDEX IF NOT EXISTS ix_cost_savings_v4_id ON cost_savings_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_cost_savings_v4_organization_id ON cost_savings_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_creator_profiles_id ON creator_profiles (id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_creator_profiles_user_id ON creator_profiles (user_id);
    CREATE INDEX IF NOT EXISTS ix_credit_transactions_id ON credit_transactions (id);
    CREATE INDEX IF NOT EXISTS ix_credit_transactions_organization_id ON credit_transactions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_credit_transactions_user_id ON credit_transactions (user_id);
    CREATE INDEX IF NOT EXISTS ix_custom_connector_endpoints_id ON custom_connector_endpoints (id);
    CREATE INDEX IF NOT EXISTS ix_custom_connector_endpoints_organization_id ON custom_connector_endpoints (organization_id);
    CREATE INDEX IF NOT EXISTS ix_data_residency_configs_id ON data_residency_configs (id);
    CREATE INDEX IF NOT EXISTS ix_data_residency_configs_organization_id ON data_residency_configs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_data_residency_configs_region_id ON data_residency_configs (region_id);
    CREATE INDEX IF NOT EXISTS ix_device_schedules_device_id ON device_schedules (device_id);
    CREATE INDEX IF NOT EXISTS ix_device_schedules_id ON device_schedules (id);
    CREATE INDEX IF NOT EXISTS ix_device_telemetry_device_id ON device_telemetry (device_id);
    CREATE INDEX IF NOT EXISTS ix_device_telemetry_id ON device_telemetry (id);
    CREATE INDEX IF NOT EXISTS ix_digital_twins_id ON digital_twins (id);
    CREATE INDEX IF NOT EXISTS ix_digital_twins_organization_id ON digital_twins (organization_id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_analytics_v4_id ON enterprise_analytics_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_analytics_v4_organization_id ON enterprise_analytics_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_integrations_v4_id ON enterprise_integrations_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_integrations_v4_organization_id ON enterprise_integrations_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_financial_records_id ON financial_records (id);
    CREATE INDEX IF NOT EXISTS ix_financial_records_organization_id ON financial_records (organization_id);
    CREATE INDEX IF NOT EXISTS ix_industry_agents_agent_type ON industry_agents (agent_type);
    CREATE INDEX IF NOT EXISTS ix_industry_agents_id ON industry_agents (id);
    CREATE INDEX IF NOT EXISTS ix_industry_agents_industry_id ON industry_agents (industry_id);
    CREATE INDEX IF NOT EXISTS ix_industry_analytics_id ON industry_analytics (id);
    CREATE INDEX IF NOT EXISTS ix_industry_analytics_industry_id ON industry_analytics (industry_id);
    CREATE INDEX IF NOT EXISTS ix_industry_analytics_metric_type ON industry_analytics (metric_type);
    CREATE INDEX IF NOT EXISTS ix_industry_compliance_packs_id ON industry_compliance_packs (id);
    CREATE INDEX IF NOT EXISTS ix_industry_knowledge_bases_category ON industry_knowledge_bases (category);
    CREATE INDEX IF NOT EXISTS ix_industry_knowledge_bases_id ON industry_knowledge_bases (id);
    CREATE INDEX IF NOT EXISTS ix_industry_knowledge_bases_industry_id ON industry_knowledge_bases (industry_id);
    CREATE INDEX IF NOT EXISTS ix_industry_templates_id ON industry_templates (id);
    CREATE INDEX IF NOT EXISTS ix_industry_templates_industry_id ON industry_templates (industry_id);
    CREATE INDEX IF NOT EXISTS ix_industry_templates_template_type ON industry_templates (template_type);
    CREATE INDEX IF NOT EXISTS ix_industry_workflows_id ON industry_workflows (id);
    CREATE INDEX IF NOT EXISTS ix_industry_workflows_industry_id ON industry_workflows (industry_id);
    CREATE INDEX IF NOT EXISTS ix_industry_workflows_workflow_type ON industry_workflows (workflow_type);
    CREATE INDEX IF NOT EXISTS ix_knowledge_connectors_id ON knowledge_connectors (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_connectors_organization_id ON knowledge_connectors (organization_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_connectors_v5_id ON knowledge_connectors_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_connectors_v5_organization_id ON knowledge_connectors_v5 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_id ON knowledge_documents (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_organization_id ON knowledge_documents (organization_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_graph_nodes_id ON knowledge_graph_nodes (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_graph_nodes_organization_id ON knowledge_graph_nodes (organization_id);
    CREATE INDEX IF NOT EXISTS ix_marketplace_connectors_id ON marketplace_connectors (id);
    CREATE INDEX IF NOT EXISTS ix_media_assets_id ON media_assets (id);
    CREATE INDEX IF NOT EXISTS ix_media_assets_user_id ON media_assets (user_id);
    CREATE INDEX IF NOT EXISTS ix_model_registry_v4_id ON model_registry_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_model_registry_v4_organization_id ON model_registry_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_multimodal_conversations_id ON multimodal_conversations (id);
    CREATE INDEX IF NOT EXISTS ix_multimodal_conversations_user_id ON multimodal_conversations (user_id);
    CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id);
    CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
    CREATE INDEX IF NOT EXISTS ix_oauth_accounts_id ON oauth_accounts (id);
    CREATE INDEX IF NOT EXISTS ix_oauth_accounts_user_id ON oauth_accounts (user_id);
    CREATE INDEX IF NOT EXISTS ix_observability_dashboards_id ON observability_dashboards (id);
    CREATE INDEX IF NOT EXISTS ix_observability_dashboards_organization_id ON observability_dashboards (organization_id);
    CREATE INDEX IF NOT EXISTS ix_organization_members_id ON organization_members (id);
    CREATE INDEX IF NOT EXISTS ix_personal_knowledge_items_assistant_id ON personal_knowledge_items (assistant_id);
    CREATE INDEX IF NOT EXISTS ix_personal_knowledge_items_id ON personal_knowledge_items (id);
    CREATE INDEX IF NOT EXISTS ix_personal_knowledge_items_user_id ON personal_knowledge_items (user_id);
    CREATE INDEX IF NOT EXISTS ix_personal_memories_assistant_id ON personal_memories (assistant_id);
    CREATE INDEX IF NOT EXISTS ix_personal_memories_id ON personal_memories (id);
    CREATE INDEX IF NOT EXISTS ix_personal_memories_user_id ON personal_memories (user_id);
    CREATE INDEX IF NOT EXISTS ix_personal_tasks_assistant_id ON personal_tasks (assistant_id);
    CREATE INDEX IF NOT EXISTS ix_personal_tasks_id ON personal_tasks (id);
    CREATE INDEX IF NOT EXISTS ix_personal_tasks_user_id ON personal_tasks (user_id);
    CREATE INDEX IF NOT EXISTS ix_plugin_definitions_v4_id ON plugin_definitions_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_plugin_definitions_v4_publisher_id ON plugin_definitions_v4 (publisher_id);
    CREATE INDEX IF NOT EXISTS ix_policies_id ON policies (id);
    CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id);
    CREATE INDEX IF NOT EXISTS ix_projects_organization_id ON projects (organization_id);
    CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_registry_category ON prompt_registry (category, status);
    CREATE INDEX IF NOT EXISTS ix_prompt_registry_category ON prompt_registry (category);
    CREATE INDEX IF NOT EXISTS ix_prompt_registry_name ON prompt_registry (name);
    CREATE INDEX IF NOT EXISTS ix_regulations_id ON regulations (id);
    CREATE INDEX IF NOT EXISTS ix_risk_scores_id ON risk_scores (id);
    CREATE INDEX IF NOT EXISTS ix_search_queries_v5_id ON search_queries_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_search_queries_v5_organization_id ON search_queries_v5 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_search_queries_v5_user_id ON search_queries_v5 (user_id);
    CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events_v6 (severity, event_timestamp);
    CREATE INDEX IF NOT EXISTS idx_security_events_type_time ON security_events_v6 (event_type, event_timestamp);
    CREATE INDEX IF NOT EXISTS idx_security_events_user_time ON security_events_v6 (user_id, event_timestamp);
    CREATE INDEX IF NOT EXISTS ix_security_events_v6_event_timestamp ON security_events_v6 (event_timestamp);
    CREATE INDEX IF NOT EXISTS ix_security_events_v6_event_type ON security_events_v6 (event_type);
    CREATE INDEX IF NOT EXISTS ix_security_events_v6_organization_id ON security_events_v6 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_security_events_v6_user_id ON security_events_v6 (user_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_models_id ON simulation_models (id);
    CREATE INDEX IF NOT EXISTS ix_simulation_models_organization_id ON simulation_models (organization_id);
    CREATE INDEX IF NOT EXISTS ix_solution_packages_id ON solution_packages (id);
    CREATE INDEX IF NOT EXISTS ix_solution_packages_industry_id ON solution_packages (industry_id);
    CREATE INDEX IF NOT EXISTS ix_studio_projects_id ON studio_projects (id);
    CREATE INDEX IF NOT EXISTS ix_studio_projects_organization_id ON studio_projects (organization_id);
    CREATE INDEX IF NOT EXISTS ix_studio_projects_user_id ON studio_projects (user_id);
    CREATE INDEX IF NOT EXISTS ix_tenant_environments_id ON tenant_environments (id);
    CREATE INDEX IF NOT EXISTS ix_tenant_environments_organization_id ON tenant_environments (organization_id);
    CREATE INDEX IF NOT EXISTS ix_usage_logs_id ON usage_logs (id);
    CREATE INDEX IF NOT EXISTS ix_usage_logs_organization_id ON usage_logs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id ON usage_logs (user_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_installations_v4_id ON workflow_installations_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_workflow_installations_v4_organization_id ON workflow_installations_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_installations_v4_template_id ON workflow_installations_v4 (template_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_installations_v4_tenant_id ON workflow_installations_v4 (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_ratings_v4_id ON workflow_ratings_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_workflow_ratings_v4_template_id ON workflow_ratings_v4 (template_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_ratings_v4_user_id ON workflow_ratings_v4 (user_id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_analytics_agent_id ON agent_analytics (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_analytics_id ON agent_analytics (id);
    CREATE INDEX IF NOT EXISTS ix_agent_approval_requests_agent_id ON agent_approval_requests (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_approval_requests_id ON agent_approval_requests (id);
    CREATE INDEX IF NOT EXISTS ix_agent_approval_requests_organization_id ON agent_approval_requests (organization_id);
    CREATE INDEX IF NOT EXISTS ix_agent_approval_requests_requested_by ON agent_approval_requests (requested_by);
    CREATE INDEX IF NOT EXISTS ix_agent_memories_agent_id ON agent_memories (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_memories_id ON agent_memories (id);
    CREATE INDEX IF NOT EXISTS ix_agent_memories_key ON agent_memories (key);
    CREATE INDEX IF NOT EXISTS ix_agent_memories_user_id ON agent_memories (user_id);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_agent_id ON agent_memory_network (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_id ON agent_memory_network (id);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_key ON agent_memory_network (key);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_organization_id ON agent_memory_network (organization_id);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_team_id ON agent_memory_network (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_memory_network_user_id ON agent_memory_network (user_id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_performance_agent_id ON agent_performance (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_performance_id ON agent_performance (id);
    CREATE INDEX IF NOT EXISTS ix_agent_performance_team_id ON agent_performance (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_permissions_agent_id ON agent_permissions (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_permissions_id ON agent_permissions (id);
    CREATE INDEX IF NOT EXISTS ix_agent_permissions_team_id ON agent_permissions (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_session_links_agent_id ON agent_session_links (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_session_links_id ON agent_session_links (id);
    CREATE INDEX IF NOT EXISTS ix_agent_session_links_session_id ON agent_session_links (session_id);
    CREATE INDEX IF NOT EXISTS ix_agent_skills_agent_id ON agent_skills (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_skills_id ON agent_skills (id);
    CREATE INDEX IF NOT EXISTS ix_agent_task_delegations_assignee_id ON agent_task_delegations (assignee_id);
    CREATE INDEX IF NOT EXISTS ix_agent_task_delegations_assignor_id ON agent_task_delegations (assignor_id);
    CREATE INDEX IF NOT EXISTS ix_agent_task_delegations_id ON agent_task_delegations (id);
    CREATE INDEX IF NOT EXISTS ix_agent_task_delegations_parent_task_id ON agent_task_delegations (parent_task_id);
    CREATE INDEX IF NOT EXISTS ix_agent_task_delegations_team_id ON agent_task_delegations (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_tasks_agent_id ON agent_tasks (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_tasks_id ON agent_tasks (id);
    CREATE INDEX IF NOT EXISTS ix_agent_tasks_parent_task_id ON agent_tasks (parent_task_id);
    CREATE INDEX IF NOT EXISTS ix_agent_tasks_user_id ON agent_tasks (user_id);
    CREATE INDEX IF NOT EXISTS ix_agent_team_members_agent_id ON agent_team_members (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_team_members_id ON agent_team_members (id);
    CREATE INDEX IF NOT EXISTS ix_agent_team_members_team_id ON agent_team_members (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_tools_agent_id ON agent_tools (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_tools_id ON agent_tools (id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_insights_id ON ai_meeting_insights (id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_insights_organization_id ON ai_meeting_insights (organization_id);
    CREATE INDEX IF NOT EXISTS ix_ai_meeting_insights_session_id ON ai_meeting_insights (session_id);
    CREATE INDEX IF NOT EXISTS ix_app_components_v4_app_id ON app_components_v4 (app_id);
    CREATE INDEX IF NOT EXISTS ix_app_components_v4_id ON app_components_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_app_installations_app_id ON app_installations (app_id);
    CREATE INDEX IF NOT EXISTS ix_app_installations_id ON app_installations (id);
    CREATE INDEX IF NOT EXISTS ix_app_installations_organization_id ON app_installations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_app_installations_tenant_id ON app_installations (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_app_purchases_app_id ON app_purchases (app_id);
    CREATE INDEX IF NOT EXISTS ix_app_purchases_id ON app_purchases (id);
    CREATE INDEX IF NOT EXISTS ix_app_purchases_organization_id ON app_purchases (organization_id);
    CREATE INDEX IF NOT EXISTS ix_app_purchases_tenant_id ON app_purchases (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_app_reviews_v4_app_id ON app_reviews_v4 (app_id);
    CREATE INDEX IF NOT EXISTS ix_app_reviews_v4_id ON app_reviews_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_app_reviews_v4_user_id ON app_reviews_v4 (user_id);
    CREATE INDEX IF NOT EXISTS ix_backup_records_v4_id ON backup_records_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_backup_records_v4_tenant_id ON backup_records_v4 (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_bots_id ON bots (id);
    CREATE INDEX IF NOT EXISTS ix_bots_project_id ON bots (project_id);
    CREATE INDEX IF NOT EXISTS ix_bots_user_id ON bots (user_id);
    CREATE INDEX IF NOT EXISTS ix_build_records_id ON build_records (id);
    CREATE INDEX IF NOT EXISTS ix_build_records_project_id ON build_records (project_id);
    CREATE INDEX IF NOT EXISTS ix_build_records_user_id ON build_records (user_id);
    CREATE INDEX IF NOT EXISTS ix_business_workflow_executions_id ON business_workflow_executions (id);
    CREATE INDEX IF NOT EXISTS ix_business_workflow_executions_organization_id ON business_workflow_executions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_business_workflow_executions_workflow_id ON business_workflow_executions (workflow_id);
    CREATE INDEX IF NOT EXISTS ix_chat_messages_id ON chat_messages (id);
    CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages (session_id);
    CREATE INDEX IF NOT EXISTS ix_code_projects_id ON code_projects (id);
    CREATE INDEX IF NOT EXISTS ix_code_projects_project_id ON code_projects (project_id);
    CREATE INDEX IF NOT EXISTS ix_code_projects_user_id ON code_projects (user_id);
    CREATE INDEX IF NOT EXISTS ix_collab_multimodal_messages_id ON collab_multimodal_messages (id);
    CREATE INDEX IF NOT EXISTS ix_collab_multimodal_messages_session_id ON collab_multimodal_messages (session_id);
    CREATE INDEX IF NOT EXISTS ix_compliance_check_results_id ON compliance_check_results (id);
    CREATE INDEX IF NOT EXISTS ix_connector_credentials_id ON connector_credentials (id);
    CREATE INDEX IF NOT EXISTS ix_connector_credentials_integration_id ON connector_credentials (integration_id);
    CREATE INDEX IF NOT EXISTS ix_connector_logs_id ON connector_logs (id);
    CREATE INDEX IF NOT EXISTS ix_connector_logs_integration_id ON connector_logs (integration_id);
    CREATE INDEX IF NOT EXISTS ix_connector_logs_organization_id ON connector_logs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_connector_permissions_id ON connector_permissions (id);
    CREATE INDEX IF NOT EXISTS ix_connector_permissions_integration_id ON connector_permissions (integration_id);
    CREATE INDEX IF NOT EXISTS ix_connector_permissions_organization_id ON connector_permissions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_analytics_copilot_id ON copilot_analytics (copilot_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_analytics_id ON copilot_analytics (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_analytics_organization_id ON copilot_analytics (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_analytics_user_id ON copilot_analytics (user_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_knowledge_links_copilot_id ON copilot_knowledge_links (copilot_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_knowledge_links_id ON copilot_knowledge_links (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_knowledge_links_organization_id ON copilot_knowledge_links (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_sessions_copilot_id ON copilot_sessions (copilot_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_sessions_id ON copilot_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_sessions_organization_id ON copilot_sessions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_sessions_user_id ON copilot_sessions (user_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflows_copilot_id ON copilot_workflows (copilot_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflows_id ON copilot_workflows (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflows_organization_id ON copilot_workflows (organization_id);
    CREATE INDEX IF NOT EXISTS ix_department_agents_department_id ON department_agents (department_id);
    CREATE INDEX IF NOT EXISTS ix_department_agents_id ON department_agents (id);
    CREATE INDEX IF NOT EXISTS ix_dev_projects_id ON dev_projects (id);
    CREATE INDEX IF NOT EXISTS ix_dev_projects_organization_id ON dev_projects (organization_id);
    CREATE INDEX IF NOT EXISTS ix_dev_projects_team_id ON dev_projects (team_id);
    CREATE INDEX IF NOT EXISTS ix_dev_projects_user_id ON dev_projects (user_id);
    CREATE INDEX IF NOT EXISTS ix_digital_twin_entities_id ON digital_twin_entities (id);
    CREATE INDEX IF NOT EXISTS ix_digital_twin_entities_twin_id ON digital_twin_entities (twin_id);
    CREATE INDEX IF NOT EXISTS ix_disaster_recovery_plans_id ON disaster_recovery_plans (id);
    CREATE INDEX IF NOT EXISTS ix_disaster_recovery_plans_tenant_id ON disaster_recovery_plans (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_document_collaborations_id ON document_collaborations (id);
    CREATE INDEX IF NOT EXISTS ix_document_collaborations_session_id ON document_collaborations (session_id);
    CREATE INDEX IF NOT EXISTS ix_documents_id ON documents (id);
    CREATE INDEX IF NOT EXISTS ix_documents_project_id ON documents (project_id);
    CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents (user_id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_listings_id ON enterprise_listings (id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_listings_organization_id ON enterprise_listings (organization_id);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_listings_product_id ON enterprise_listings (product_id);
    CREATE INDEX IF NOT EXISTS ix_findings_id ON findings (id);
    CREATE INDEX IF NOT EXISTS ix_fine_tuned_models_v4_base_model_id ON fine_tuned_models_v4 (base_model_id);
    CREATE INDEX IF NOT EXISTS ix_fine_tuned_models_v4_id ON fine_tuned_models_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_fine_tuned_models_v4_organization_id ON fine_tuned_models_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_human_reviews_reviewer_id ON human_reviews (reviewer_id);
    CREATE INDEX IF NOT EXISTS ix_integration_auth_v4_id ON integration_auth_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_integration_auth_v4_integration_id ON integration_auth_v4 (integration_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_v5_connector_id ON knowledge_documents_v5 (connector_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_v5_id ON knowledge_documents_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_v5_organization_id ON knowledge_documents_v5 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_graph_edges_id ON knowledge_graph_edges (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_graph_edges_source_node_id ON knowledge_graph_edges (source_node_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_graph_edges_target_node_id ON knowledge_graph_edges (target_node_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_sources_v4_connector_id ON knowledge_sources_v4 (connector_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_sources_v4_id ON knowledge_sources_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_model_benchmarks_v4_id ON model_benchmarks_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_model_benchmarks_v4_model_id ON model_benchmarks_v4 (model_id);
    CREATE INDEX IF NOT EXISTS ix_monitoring_metrics_cluster_id ON monitoring_metrics (cluster_id);
    CREATE INDEX IF NOT EXISTS ix_monitoring_metrics_id ON monitoring_metrics (id);
    CREATE INDEX IF NOT EXISTS ix_monitoring_metrics_metric_name ON monitoring_metrics (metric_name);
    CREATE INDEX IF NOT EXISTS ix_monitoring_metrics_region_id ON monitoring_metrics (region_id);
    CREATE INDEX IF NOT EXISTS ix_multimodal_messages_conversation_id ON multimodal_messages (conversation_id);
    CREATE INDEX IF NOT EXISTS ix_multimodal_messages_id ON multimodal_messages (id);
    CREATE INDEX IF NOT EXISTS ix_ocr_results_asset_id ON ocr_results (asset_id);
    CREATE INDEX IF NOT EXISTS ix_ocr_results_id ON ocr_results (id);
    CREATE INDEX IF NOT EXISTS ix_plugin_definitions_author_id ON plugin_definitions (author_id);
    CREATE INDEX IF NOT EXISTS ix_plugin_definitions_id ON plugin_definitions (id);
    CREATE INDEX IF NOT EXISTS ix_product_analytics_id ON product_analytics (id);
    CREATE INDEX IF NOT EXISTS ix_product_analytics_product_id ON product_analytics (product_id);
    CREATE INDEX IF NOT EXISTS ix_product_reviews_id ON product_reviews (id);
    CREATE INDEX IF NOT EXISTS ix_product_reviews_product_id ON product_reviews (product_id);
    CREATE INDEX IF NOT EXISTS ix_product_reviews_user_id ON product_reviews (user_id);
    CREATE INDEX IF NOT EXISTS ix_product_versions_id ON product_versions (id);
    CREATE INDEX IF NOT EXISTS ix_product_versions_product_id ON product_versions (product_id);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_version_prompt ON prompt_versions (prompt_id, version);
    CREATE INDEX IF NOT EXISTS ix_prompt_versions_prompt_id ON prompt_versions (prompt_id);
    CREATE INDEX IF NOT EXISTS ix_published_apps_v4_app_id ON published_apps_v4 (app_id);
    CREATE INDEX IF NOT EXISTS ix_published_apps_v4_id ON published_apps_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_published_apps_v4_organization_id ON published_apps_v4 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_regional_deployments_id ON regional_deployments (id);
    CREATE INDEX IF NOT EXISTS ix_regional_deployments_tenant_id ON regional_deployments (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_regulatory_updates_id ON regulatory_updates (id);
    CREATE INDEX IF NOT EXISTS ix_repositories_id ON repositories (id);
    CREATE INDEX IF NOT EXISTS ix_repositories_project_id ON repositories (project_id);
    CREATE INDEX IF NOT EXISTS ix_repositories_user_id ON repositories (user_id);
    CREATE INDEX IF NOT EXISTS ix_scenarios_id ON scenarios (id);
    CREATE INDEX IF NOT EXISTS ix_scenarios_model_id ON scenarios (model_id);
    CREATE INDEX IF NOT EXISTS ix_scenarios_organization_id ON scenarios (organization_id);
    CREATE INDEX IF NOT EXISTS ix_scenarios_twin_id ON scenarios (twin_id);
    CREATE INDEX IF NOT EXISTS ix_screen_share_sessions_id ON screen_share_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_screen_share_sessions_session_id ON screen_share_sessions (session_id);
    CREATE INDEX IF NOT EXISTS ix_security_scans_id ON security_scans (id);
    CREATE INDEX IF NOT EXISTS ix_security_scans_project_id ON security_scans (project_id);
    CREATE INDEX IF NOT EXISTS ix_security_scans_user_id ON security_scans (user_id);
    CREATE INDEX IF NOT EXISTS ix_service_deployments_cluster_id ON service_deployments (cluster_id);
    CREATE INDEX IF NOT EXISTS ix_service_deployments_id ON service_deployments (id);
    CREATE INDEX IF NOT EXISTS ix_session_participants_id ON session_participants (id);
    CREATE INDEX IF NOT EXISTS ix_session_participants_session_id ON session_participants (session_id);
    CREATE INDEX IF NOT EXISTS ix_session_recordings_id ON session_recordings (id);
    CREATE INDEX IF NOT EXISTS ix_session_recordings_session_id ON session_recordings (session_id);
    CREATE INDEX IF NOT EXISTS ix_studio_documentations_id ON studio_documentations (id);
    CREATE INDEX IF NOT EXISTS ix_studio_documentations_project_id ON studio_documentations (project_id);
    CREATE INDEX IF NOT EXISTS ix_studio_documentations_user_id ON studio_documentations (user_id);
    CREATE INDEX IF NOT EXISTS ix_studio_files_id ON studio_files (id);
    CREATE INDEX IF NOT EXISTS ix_studio_files_project_id ON studio_files (project_id);
    CREATE INDEX IF NOT EXISTS ix_sync_jobs_id ON sync_jobs (id);
    CREATE INDEX IF NOT EXISTS ix_sync_jobs_integration_id ON sync_jobs (integration_id);
    CREATE INDEX IF NOT EXISTS ix_sync_jobs_organization_id ON sync_jobs (organization_id);
    CREATE INDEX IF NOT EXISTS ix_sync_records_v4_id ON sync_records_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_sync_records_v4_integration_id ON sync_records_v4 (integration_id);
    CREATE INDEX IF NOT EXISTS ix_test_runs_id ON test_runs (id);
    CREATE INDEX IF NOT EXISTS ix_test_runs_project_id ON test_runs (project_id);
    CREATE INDEX IF NOT EXISTS ix_test_runs_user_id ON test_runs (user_id);
    CREATE INDEX IF NOT EXISTS ix_usage_metrics_v4_id ON usage_metrics_v4 (id);
    CREATE INDEX IF NOT EXISTS ix_usage_metrics_v4_metric_name ON usage_metrics_v4 (metric_name);
    CREATE INDEX IF NOT EXISTS ix_usage_metrics_v4_tenant_id ON usage_metrics_v4 (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_user_feedback_user_id ON user_feedback (user_id);
    CREATE INDEX IF NOT EXISTS ix_verification_results_id ON verification_results (id);
    CREATE INDEX IF NOT EXISTS ix_verification_results_product_id ON verification_results (product_id);
    CREATE INDEX IF NOT EXISTS ix_video_jobs_id ON video_jobs (id);
    CREATE INDEX IF NOT EXISTS ix_video_jobs_user_id ON video_jobs (user_id);
    CREATE INDEX IF NOT EXISTS ix_voice_sessions_id ON voice_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_voice_sessions_organization_id ON voice_sessions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_voice_sessions_user_id ON voice_sessions (user_id);
    CREATE INDEX IF NOT EXISTS ix_webhook_events_id ON webhook_events (id);
    CREATE INDEX IF NOT EXISTS ix_webhook_events_integration_id ON webhook_events (integration_id);
    CREATE INDEX IF NOT EXISTS ix_webhook_events_organization_id ON webhook_events (organization_id);
    CREATE INDEX IF NOT EXISTS ix_websites_id ON websites (id);
    CREATE INDEX IF NOT EXISTS ix_websites_project_id ON websites (project_id);
    CREATE INDEX IF NOT EXISTS ix_websites_user_id ON websites (user_id);
    CREATE INDEX IF NOT EXISTS ix_whiteboard_sessions_id ON whiteboard_sessions (id);
    CREATE INDEX IF NOT EXISTS ix_whiteboard_sessions_session_id ON whiteboard_sessions (session_id);
    CREATE INDEX IF NOT EXISTS ix_workflows_agent_id ON workflows (agent_id);
    CREATE INDEX IF NOT EXISTS ix_workflows_id ON workflows (id);
    CREATE INDEX IF NOT EXISTS ix_workflows_user_id ON workflows (user_id);
    CREATE INDEX IF NOT EXISTS ix_agent_executions_agent_id ON agent_executions (agent_id);
    CREATE INDEX IF NOT EXISTS ix_agent_executions_id ON agent_executions (id);
    CREATE INDEX IF NOT EXISTS ix_agent_executions_task_id ON agent_executions (task_id);
    CREATE INDEX IF NOT EXISTS ix_agent_executions_user_id ON agent_executions (user_id);
    CREATE INDEX IF NOT EXISTS ix_agent_messages_id ON agent_messages (id);
    CREATE INDEX IF NOT EXISTS ix_agent_messages_receiver_id ON agent_messages (receiver_id);
    CREATE INDEX IF NOT EXISTS ix_agent_messages_sender_id ON agent_messages (sender_id);
    CREATE INDEX IF NOT EXISTS ix_agent_messages_task_id ON agent_messages (task_id);
    CREATE INDEX IF NOT EXISTS ix_agent_messages_team_id ON agent_messages (team_id);
    CREATE INDEX IF NOT EXISTS ix_agent_reviews_id ON agent_reviews (id);
    CREATE INDEX IF NOT EXISTS ix_agent_reviews_reviewee_id ON agent_reviews (reviewee_id);
    CREATE INDEX IF NOT EXISTS ix_agent_reviews_reviewer_id ON agent_reviews (reviewer_id);
    CREATE INDEX IF NOT EXISTS ix_agent_reviews_task_id ON agent_reviews (task_id);
    CREATE INDEX IF NOT EXISTS ix_bot_conversations_bot_id ON bot_conversations (bot_id);
    CREATE INDEX IF NOT EXISTS ix_bot_conversations_id ON bot_conversations (id);
    CREATE INDEX IF NOT EXISTS ix_bot_conversations_session_id ON bot_conversations (session_id);
    CREATE INDEX IF NOT EXISTS ix_branch_records_id ON branch_records (id);
    CREATE INDEX IF NOT EXISTS ix_branch_records_repository_id ON branch_records (repository_id);
    CREATE INDEX IF NOT EXISTS ix_code_generations_code_project_id ON code_generations (code_project_id);
    CREATE INDEX IF NOT EXISTS ix_code_generations_id ON code_generations (id);
    CREATE INDEX IF NOT EXISTS ix_commit_records_id ON commit_records (id);
    CREATE INDEX IF NOT EXISTS ix_commit_records_repository_id ON commit_records (repository_id);
    CREATE INDEX IF NOT EXISTS ix_commit_records_user_id ON commit_records (user_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_approvals_id ON copilot_approvals (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_approvals_organization_id ON copilot_approvals (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_approvals_session_id ON copilot_approvals (session_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_messages_id ON copilot_messages (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_messages_session_id ON copilot_messages (session_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_recommendations_id ON copilot_recommendations (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_recommendations_organization_id ON copilot_recommendations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_recommendations_session_id ON copilot_recommendations (session_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_recommendations_user_id ON copilot_recommendations (user_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflow_executions_id ON copilot_workflow_executions (id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflow_executions_organization_id ON copilot_workflow_executions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflow_executions_user_id ON copilot_workflow_executions (user_id);
    CREATE INDEX IF NOT EXISTS ix_copilot_workflow_executions_workflow_id ON copilot_workflow_executions (workflow_id);
    CREATE INDEX IF NOT EXISTS ix_corrective_actions_id ON corrective_actions (id);
    CREATE INDEX IF NOT EXISTS ix_document_versions_document_id ON document_versions (document_id);
    CREATE INDEX IF NOT EXISTS ix_document_versions_id ON document_versions (id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_documents_id ON enterprise_documents (id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_documents_organization_id ON enterprise_documents (organization_id);
    CREATE INDEX IF NOT EXISTS ix_enterprise_documents_source_id ON enterprise_documents (source_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_v5_document_id ON knowledge_chunks_v5 (document_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_v5_id ON knowledge_chunks_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_permissions_v5_document_id ON knowledge_permissions_v5 (document_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_permissions_v5_id ON knowledge_permissions_v5 (id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_permissions_v5_organization_id ON knowledge_permissions_v5 (organization_id);
    CREATE INDEX IF NOT EXISTS ix_knowledge_permissions_v5_principal_id ON knowledge_permissions_v5 (principal_id);
    CREATE INDEX IF NOT EXISTS ix_plugin_installations_id ON plugin_installations (id);
    CREATE INDEX IF NOT EXISTS ix_plugin_installations_organization_id ON plugin_installations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_plugin_installations_plugin_id ON plugin_installations (plugin_id);
    CREATE INDEX IF NOT EXISTS ix_plugin_installations_user_id ON plugin_installations (user_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_variables_id ON simulation_variables (id);
    CREATE INDEX IF NOT EXISTS ix_simulation_variables_scenario_id ON simulation_variables (scenario_id);
    CREATE INDEX IF NOT EXISTS ix_simulations_id ON simulations (id);
    CREATE INDEX IF NOT EXISTS ix_simulations_organization_id ON simulations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_simulations_scenario_id ON simulations (scenario_id);
    CREATE INDEX IF NOT EXISTS ix_simulations_user_id ON simulations (user_id);
    CREATE INDEX IF NOT EXISTS ix_studio_deployments_id ON studio_deployments (id);
    CREATE INDEX IF NOT EXISTS ix_studio_deployments_project_id ON studio_deployments (project_id);
    CREATE INDEX IF NOT EXISTS ix_studio_deployments_user_id ON studio_deployments (user_id);
    CREATE INDEX IF NOT EXISTS ix_voice_messages_id ON voice_messages (id);
    CREATE INDEX IF NOT EXISTS ix_voice_messages_session_id ON voice_messages (session_id);
    CREATE INDEX IF NOT EXISTS ix_website_deployments_id ON website_deployments (id);
    CREATE INDEX IF NOT EXISTS ix_website_deployments_website_id ON website_deployments (website_id);
    CREATE INDEX IF NOT EXISTS ix_workflow_steps_id ON workflow_steps (id);
    CREATE INDEX IF NOT EXISTS ix_workflow_steps_workflow_id ON workflow_steps (workflow_id);
    CREATE INDEX IF NOT EXISTS ix_bot_messages_conversation_id ON bot_messages (conversation_id);
    CREATE INDEX IF NOT EXISTS ix_bot_messages_id ON bot_messages (id);
    CREATE INDEX IF NOT EXISTS ix_citation_records_document_id ON citation_records (document_id);
    CREATE INDEX IF NOT EXISTS ix_citation_records_id ON citation_records (id);
    CREATE INDEX IF NOT EXISTS ix_citation_records_organization_id ON citation_records (organization_id);
    CREATE INDEX IF NOT EXISTS ix_citation_records_search_query_id ON citation_records (search_query_id);
    CREATE INDEX IF NOT EXISTS ix_citation_records_user_id ON citation_records (user_id);
    CREATE INDEX IF NOT EXISTS ix_predictions_id ON predictions (id);
    CREATE INDEX IF NOT EXISTS ix_predictions_organization_id ON predictions (organization_id);
    CREATE INDEX IF NOT EXISTS ix_predictions_simulation_id ON predictions (simulation_id);
    CREATE INDEX IF NOT EXISTS ix_risk_assessments_id ON risk_assessments (id);
    CREATE INDEX IF NOT EXISTS ix_risk_assessments_organization_id ON risk_assessments (organization_id);
    CREATE INDEX IF NOT EXISTS ix_risk_assessments_simulation_id ON risk_assessments (simulation_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_outcomes_id ON simulation_outcomes (id);
    CREATE INDEX IF NOT EXISTS ix_simulation_outcomes_scenario_id ON simulation_outcomes (scenario_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_outcomes_simulation_id ON simulation_outcomes (simulation_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_recommendations_id ON simulation_recommendations (id);
    CREATE INDEX IF NOT EXISTS ix_simulation_recommendations_organization_id ON simulation_recommendations (organization_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_recommendations_simulation_id ON simulation_recommendations (simulation_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_reports_id ON simulation_reports (id);
    CREATE INDEX IF NOT EXISTS ix_simulation_reports_organization_id ON simulation_reports (organization_id);
    CREATE INDEX IF NOT EXISTS ix_simulation_reports_simulation_id ON simulation_reports (simulation_id);
    """))



def downgrade() -> None:
    # Drop the adopted tables in reverse dependency order. CASCADE also
    # releases FK constraints held by the 0002-managed tables.
    op.execute(sa.text("""
    DROP TABLE IF EXISTS "simulation_reports" CASCADE;
    DROP TABLE IF EXISTS "simulation_recommendations" CASCADE;
    DROP TABLE IF EXISTS "simulation_outcomes" CASCADE;
    DROP TABLE IF EXISTS "risk_assessments" CASCADE;
    DROP TABLE IF EXISTS "predictions" CASCADE;
    DROP TABLE IF EXISTS "citation_records" CASCADE;
    DROP TABLE IF EXISTS "bot_messages" CASCADE;
    DROP TABLE IF EXISTS "workflow_steps" CASCADE;
    DROP TABLE IF EXISTS "website_deployments" CASCADE;
    DROP TABLE IF EXISTS "voice_messages" CASCADE;
    DROP TABLE IF EXISTS "studio_deployments" CASCADE;
    DROP TABLE IF EXISTS "simulations" CASCADE;
    DROP TABLE IF EXISTS "simulation_variables" CASCADE;
    DROP TABLE IF EXISTS "plugin_installations" CASCADE;
    DROP TABLE IF EXISTS "knowledge_permissions_v5" CASCADE;
    DROP TABLE IF EXISTS "knowledge_chunks_v5" CASCADE;
    DROP TABLE IF EXISTS "enterprise_documents" CASCADE;
    DROP TABLE IF EXISTS "document_versions" CASCADE;
    DROP TABLE IF EXISTS "corrective_actions" CASCADE;
    DROP TABLE IF EXISTS "copilot_workflow_executions" CASCADE;
    DROP TABLE IF EXISTS "copilot_recommendations" CASCADE;
    DROP TABLE IF EXISTS "copilot_messages" CASCADE;
    DROP TABLE IF EXISTS "copilot_approvals" CASCADE;
    DROP TABLE IF EXISTS "commit_records" CASCADE;
    DROP TABLE IF EXISTS "code_generations" CASCADE;
    DROP TABLE IF EXISTS "branch_records" CASCADE;
    DROP TABLE IF EXISTS "bot_conversations" CASCADE;
    DROP TABLE IF EXISTS "agent_reviews" CASCADE;
    DROP TABLE IF EXISTS "agent_messages" CASCADE;
    DROP TABLE IF EXISTS "agent_executions" CASCADE;
    DROP TABLE IF EXISTS "workflows" CASCADE;
    DROP TABLE IF EXISTS "whiteboard_sessions" CASCADE;
    DROP TABLE IF EXISTS "websites" CASCADE;
    DROP TABLE IF EXISTS "webhook_events" CASCADE;
    DROP TABLE IF EXISTS "voice_sessions" CASCADE;
    DROP TABLE IF EXISTS "video_jobs" CASCADE;
    DROP TABLE IF EXISTS "verification_results" CASCADE;
    DROP TABLE IF EXISTS "user_feedback" CASCADE;
    DROP TABLE IF EXISTS "usage_metrics_v4" CASCADE;
    DROP TABLE IF EXISTS "test_runs" CASCADE;
    DROP TABLE IF EXISTS "sync_records_v4" CASCADE;
    DROP TABLE IF EXISTS "sync_jobs" CASCADE;
    DROP TABLE IF EXISTS "studio_files" CASCADE;
    DROP TABLE IF EXISTS "studio_documentations" CASCADE;
    DROP TABLE IF EXISTS "session_recordings" CASCADE;
    DROP TABLE IF EXISTS "session_participants" CASCADE;
    DROP TABLE IF EXISTS "service_deployments" CASCADE;
    DROP TABLE IF EXISTS "security_scans" CASCADE;
    DROP TABLE IF EXISTS "screen_share_sessions" CASCADE;
    DROP TABLE IF EXISTS "scenarios" CASCADE;
    DROP TABLE IF EXISTS "repositories" CASCADE;
    DROP TABLE IF EXISTS "regulatory_updates" CASCADE;
    DROP TABLE IF EXISTS "regional_deployments" CASCADE;
    DROP TABLE IF EXISTS "published_apps_v4" CASCADE;
    DROP TABLE IF EXISTS "prompt_versions" CASCADE;
    DROP TABLE IF EXISTS "product_versions" CASCADE;
    DROP TABLE IF EXISTS "product_reviews" CASCADE;
    DROP TABLE IF EXISTS "product_analytics" CASCADE;
    DROP TABLE IF EXISTS "plugin_definitions" CASCADE;
    DROP TABLE IF EXISTS "ocr_results" CASCADE;
    DROP TABLE IF EXISTS "multimodal_messages" CASCADE;
    DROP TABLE IF EXISTS "monitoring_metrics" CASCADE;
    DROP TABLE IF EXISTS "model_benchmarks_v4" CASCADE;
    DROP TABLE IF EXISTS "knowledge_sources_v4" CASCADE;
    DROP TABLE IF EXISTS "knowledge_graph_edges" CASCADE;
    DROP TABLE IF EXISTS "knowledge_documents_v5" CASCADE;
    DROP TABLE IF EXISTS "integration_auth_v4" CASCADE;
    DROP TABLE IF EXISTS "human_reviews" CASCADE;
    DROP TABLE IF EXISTS "hallucination_events" CASCADE;
    DROP TABLE IF EXISTS "fine_tuned_models_v4" CASCADE;
    DROP TABLE IF EXISTS "findings" CASCADE;
    DROP TABLE IF EXISTS "enterprise_listings" CASCADE;
    DROP TABLE IF EXISTS "documents" CASCADE;
    DROP TABLE IF EXISTS "document_collaborations" CASCADE;
    DROP TABLE IF EXISTS "disaster_recovery_plans" CASCADE;
    DROP TABLE IF EXISTS "digital_twin_entities" CASCADE;
    DROP TABLE IF EXISTS "dev_projects" CASCADE;
    DROP TABLE IF EXISTS "department_agents" CASCADE;
    DROP TABLE IF EXISTS "copilot_workflows" CASCADE;
    DROP TABLE IF EXISTS "copilot_sessions" CASCADE;
    DROP TABLE IF EXISTS "copilot_knowledge_links" CASCADE;
    DROP TABLE IF EXISTS "copilot_analytics" CASCADE;
    DROP TABLE IF EXISTS "connector_permissions" CASCADE;
    DROP TABLE IF EXISTS "connector_logs" CASCADE;
    DROP TABLE IF EXISTS "connector_credentials" CASCADE;
    DROP TABLE IF EXISTS "compliance_check_results" CASCADE;
    DROP TABLE IF EXISTS "collab_multimodal_messages" CASCADE;
    DROP TABLE IF EXISTS "code_projects" CASCADE;
    DROP TABLE IF EXISTS "chat_messages" CASCADE;
    DROP TABLE IF EXISTS "business_workflow_executions" CASCADE;
    DROP TABLE IF EXISTS "build_records" CASCADE;
    DROP TABLE IF EXISTS "bots" CASCADE;
    DROP TABLE IF EXISTS "backup_records_v4" CASCADE;
    DROP TABLE IF EXISTS "app_reviews_v4" CASCADE;
    DROP TABLE IF EXISTS "app_purchases" CASCADE;
    DROP TABLE IF EXISTS "app_installations" CASCADE;
    DROP TABLE IF EXISTS "app_components_v4" CASCADE;
    DROP TABLE IF EXISTS "ai_meeting_insights" CASCADE;
    DROP TABLE IF EXISTS "agent_tools" CASCADE;
    DROP TABLE IF EXISTS "agent_team_members" CASCADE;
    DROP TABLE IF EXISTS "agent_tasks" CASCADE;
    DROP TABLE IF EXISTS "agent_task_delegations" CASCADE;
    DROP TABLE IF EXISTS "agent_skills" CASCADE;
    DROP TABLE IF EXISTS "agent_session_links" CASCADE;
    DROP TABLE IF EXISTS "agent_permissions" CASCADE;
    DROP TABLE IF EXISTS "agent_performance" CASCADE;
    DROP TABLE IF EXISTS "agent_memory_network" CASCADE;
    DROP TABLE IF EXISTS "agent_memories" CASCADE;
    DROP TABLE IF EXISTS "agent_approval_requests" CASCADE;
    DROP TABLE IF EXISTS "agent_analytics" CASCADE;
    DROP TABLE IF EXISTS "workflow_ratings_v4" CASCADE;
    DROP TABLE IF EXISTS "workflow_installations_v4" CASCADE;
    DROP TABLE IF EXISTS "usage_logs" CASCADE;
    DROP TABLE IF EXISTS "tenant_environments" CASCADE;
    DROP TABLE IF EXISTS "studio_projects" CASCADE;
    DROP TABLE IF EXISTS "solution_packages" CASCADE;
    DROP TABLE IF EXISTS "simulation_models" CASCADE;
    DROP TABLE IF EXISTS "security_events_v6" CASCADE;
    DROP TABLE IF EXISTS "search_queries_v5" CASCADE;
    DROP TABLE IF EXISTS "risk_scores" CASCADE;
    DROP TABLE IF EXISTS "regulations" CASCADE;
    DROP TABLE IF EXISTS "prompt_registry" CASCADE;
    DROP TABLE IF EXISTS "projects" CASCADE;
    DROP TABLE IF EXISTS "policies" CASCADE;
    DROP TABLE IF EXISTS "plugin_definitions_v4" CASCADE;
    DROP TABLE IF EXISTS "personal_tasks" CASCADE;
    DROP TABLE IF EXISTS "personal_memories" CASCADE;
    DROP TABLE IF EXISTS "personal_knowledge_items" CASCADE;
    DROP TABLE IF EXISTS "organization_members" CASCADE;
    DROP TABLE IF EXISTS "observability_dashboards" CASCADE;
    DROP TABLE IF EXISTS "oauth_accounts" CASCADE;
    DROP TABLE IF EXISTS "notifications" CASCADE;
    DROP TABLE IF EXISTS "multimodal_conversations" CASCADE;
    DROP TABLE IF EXISTS "model_registry_v4" CASCADE;
    DROP TABLE IF EXISTS "media_assets" CASCADE;
    DROP TABLE IF EXISTS "marketplace_connectors" CASCADE;
    DROP TABLE IF EXISTS "knowledge_graph_nodes" CASCADE;
    DROP TABLE IF EXISTS "knowledge_documents" CASCADE;
    DROP TABLE IF EXISTS "knowledge_connectors_v5" CASCADE;
    DROP TABLE IF EXISTS "knowledge_connectors" CASCADE;
    DROP TABLE IF EXISTS "industry_workflows" CASCADE;
    DROP TABLE IF EXISTS "industry_templates" CASCADE;
    DROP TABLE IF EXISTS "industry_knowledge_bases" CASCADE;
    DROP TABLE IF EXISTS "industry_compliance_packs" CASCADE;
    DROP TABLE IF EXISTS "industry_analytics" CASCADE;
    DROP TABLE IF EXISTS "industry_agents" CASCADE;
    DROP TABLE IF EXISTS "financial_records" CASCADE;
    DROP TABLE IF EXISTS "enterprise_integrations_v4" CASCADE;
    DROP TABLE IF EXISTS "enterprise_analytics_v4" CASCADE;
    DROP TABLE IF EXISTS "digital_twins" CASCADE;
    DROP TABLE IF EXISTS "device_telemetry" CASCADE;
    DROP TABLE IF EXISTS "device_schedules" CASCADE;
    DROP TABLE IF EXISTS "data_residency_configs" CASCADE;
    DROP TABLE IF EXISTS "custom_connector_endpoints" CASCADE;
    DROP TABLE IF EXISTS "credit_transactions" CASCADE;
    DROP TABLE IF EXISTS "creator_profiles" CASCADE;
    DROP TABLE IF EXISTS "cost_savings_v4" CASCADE;
    DROP TABLE IF EXISTS "copilot_domain_rules" CASCADE;
    DROP TABLE IF EXISTS "copilot_configs" CASCADE;
    DROP TABLE IF EXISTS "connector_integrations" CASCADE;
    DROP TABLE IF EXISTS "connector_api_keys" CASCADE;
    DROP TABLE IF EXISTS "compliance_rules" CASCADE;
    DROP TABLE IF EXISTS "compliance_reports_v5" CASCADE;
    DROP TABLE IF EXISTS "compliance_reports" CASCADE;
    DROP TABLE IF EXISTS "compliance_document_reviews" CASCADE;
    DROP TABLE IF EXISTS "compliance_checks" CASCADE;
    DROP TABLE IF EXISTS "collaboration_sessions" CASCADE;
    DROP TABLE IF EXISTS "collaboration_agents" CASCADE;
    DROP TABLE IF EXISTS "cluster_deployments" CASCADE;
    DROP TABLE IF EXISTS "chat_sessions" CASCADE;
    DROP TABLE IF EXISTS "business_workflows" CASCADE;
    DROP TABLE IF EXISTS "business_reports" CASCADE;
    DROP TABLE IF EXISTS "business_metrics" CASCADE;
    DROP TABLE IF EXISTS "business_alerts" CASCADE;
    DROP TABLE IF EXISTS "autonomous_workflows" CASCADE;
    DROP TABLE IF EXISTS "autonomous_research" CASCADE;
    DROP TABLE IF EXISTS "audit_records" CASCADE;
    DROP TABLE IF EXISTS "audit_logs" CASCADE;
    DROP TABLE IF EXISTS "approval_requests" CASCADE;
    DROP TABLE IF EXISTS "approval_histories" CASCADE;
    DROP TABLE IF EXISTS "app_listings" CASCADE;
    DROP TABLE IF EXISTS "api_keys" CASCADE;
    DROP TABLE IF EXISTS "ai_policies" CASCADE;
    DROP TABLE IF EXISTS "ai_monitoring_events_v4" CASCADE;
    DROP TABLE IF EXISTS "ai_generated_products" CASCADE;
    DROP TABLE IF EXISTS "ai_evaluations" CASCADE;
    DROP TABLE IF EXISTS "ai_departments" CASCADE;
    DROP TABLE IF EXISTS "ai_decisions" CASCADE;
    DROP TABLE IF EXISTS "ai_audit_events" CASCADE;
    DROP TABLE IF EXISTS "ai_app_definitions" CASCADE;
    DROP TABLE IF EXISTS "agent_teams" CASCADE;
    DROP TABLE IF EXISTS "agent_profiles" CASCADE;
    DROP TABLE IF EXISTS "adoption_metrics_v4" CASCADE;
    DROP TABLE IF EXISTS "workflow_templates_v4" CASCADE;
    DROP TABLE IF EXISTS "users" CASCADE;
    DROP TABLE IF EXISTS "startup_projects" CASCADE;
    DROP TABLE IF EXISTS "security_events" CASCADE;
    DROP TABLE IF EXISTS "sdk_releases_v4" CASCADE;
    DROP TABLE IF EXISTS "quality_scores" CASCADE;
    DROP TABLE IF EXISTS "product_ideas" CASCADE;
    DROP TABLE IF EXISTS "product_categories" CASCADE;
    DROP TABLE IF EXISTS "physical_devices" CASCADE;
    DROP TABLE IF EXISTS "personal_ai_assistants" CASCADE;
    DROP TABLE IF EXISTS "organizations" CASCADE;
    DROP TABLE IF EXISTS "organization_policies" CASCADE;
    DROP TABLE IF EXISTS "model_metrics" CASCADE;
    DROP TABLE IF EXISTS "learning_paths" CASCADE;
    DROP TABLE IF EXISTS "infrastructure_regions" CASCADE;
    DROP TABLE IF EXISTS "industries" CASCADE;
    DROP TABLE IF EXISTS "executive_assistants" CASCADE;
    DROP TABLE IF EXISTS "evaluation_cases" CASCADE;
    DROP TABLE IF EXISTS "developer_api_keys" CASCADE;
    DROP TABLE IF EXISTS "design_assets" CASCADE;
    DROP TABLE IF EXISTS "connector_definitions" CASCADE;
    DROP TABLE IF EXISTS "backup_records" CASCADE;
    DROP TABLE IF EXISTS "app_categories" CASCADE;
    DROP TABLE IF EXISTS "ai_organization_os" CASCADE;
    DROP TABLE IF EXISTS "ai_model_registry" CASCADE;
    DROP TABLE IF EXISTS "ai_meeting_sessions" CASCADE;
    DROP TABLE IF EXISTS "ai_communications" CASCADE;
    """))

