"""
Skill Library – 60+ production skills for AI agents.

Each skill has:
- id, name, description, category, proficiency levels, prerequisites, related tools
- Used for active agents to learn, level up, and match tasks
"""

from typing import Any

SKILL_CATEGORIES = [
    "technical",
    "cognitive",
    "creative",
    "interpersonal",
    "domain",
    "automation",
    "analysis",
    "communication",
]

SKILL_LIBRARY: list[dict[str, Any]] = [
    # ─── Technical ───────────────────────────────────────────────────────
    {
        "id": "python",
        "name": "Python Programming",
        "description": "Write, review, debug Python code, OOP, async, testing",
        "category": "technical",
        "icon": "🐍",
        "levels": {
            1: "Basic syntax, loops",
            5: "OOP, decorators, async, packages",
            10: "C-extension, metaclasses, performance optimization",
        },
        "prerequisites": [],
        "tools": ["code_execution", "file_system", "github"],
        "tags": ["programming", "backend"],
    },
    {
        "id": "javascript",
        "name": "JavaScript/TypeScript",
        "description": "Modern JS/TS, React, Node, async, type systems",
        "category": "technical",
        "icon": "🟨",
        "levels": {1: "Basic JS", 5: "React/Node + TS", 10: "Compiler, V8 internals"},
        "prerequisites": [],
        "tools": ["code_execution", "file_system"],
        "tags": ["frontend", "fullstack"],
    },
    {
        "id": "sql",
        "name": "SQL & Database",
        "description": "Query optimization, indexing, transactions, data modeling",
        "category": "technical",
        "icon": "🗄️",
        "levels": {1: "SELECT/JOIN", 5: "Window functions, CTEs, indexing", 10: "Distributed DB design"},
        "prerequisites": [],
        "tools": ["database", "data_analysis"],
        "tags": ["data", "backend"],
    },
    {
        "id": "devops",
        "name": "DevOps & SRE",
        "description": "CI/CD, Docker, K8s, monitoring, incident response",
        "category": "technical",
        "icon": "🚀",
        "levels": {1: "Basic Docker", 5: "K8s + Helm + observability", 10: "Multi-region SRE"},
        "prerequisites": [],
        "tools": ["api_call", "file_system", "slack"],
        "tags": ["infrastructure"],
    },
    {
        "id": "security",
        "name": "Security & Vulnerability Assessment",
        "description": "OWASP, penetration testing, secrets scanning, hardening",
        "category": "technical",
        "icon": "🛡️",
        "levels": {1: "OWASP top 10", 5: "Pentest, threat modeling", 10: "Zero-day research"},
        "prerequisites": ["python"],
        "tools": ["file_system", "code_execution", "api_call"],
        "tags": ["security"],
    },
    {
        "id": "api_integration",
        "name": "API Integration",
        "description": "REST, GraphQL, webhooks, OAuth, rate limiting",
        "category": "technical",
        "icon": "🔌",
        "levels": {1: "REST basics", 5: "GraphQL + webhook handling", 10: "API gateway design"},
        "prerequisites": [],
        "tools": ["api_call", "document_read"],
        "tags": ["backend"],
    },
    # ─── Cognitive ───────────────────────────────────────────────────────
    {
        "id": "research",
        "name": "Research & Synthesis",
        "description": "Systematic research, source evaluation, synthesis, citation",
        "category": "cognitive",
        "icon": "🔍",
        "levels": {1: "Basic web search", 5: "Multi-source synthesis", 10: "Original research design"},
        "prerequisites": [],
        "tools": ["web_search", "web_scrape", "document_write"],
        "tags": ["research"],
    },
    {
        "id": "critical_thinking",
        "name": "Critical Thinking",
        "description": "Logical reasoning, bias detection, argument analysis",
        "category": "cognitive",
        "icon": "🧠",
        "levels": {1: "Identify assumptions", 5: "Formal logic, fallacies", 10: "Decision theory"},
        "prerequisites": [],
        "tools": [],
        "tags": ["thinking"],
    },
    {
        "id": "data_analysis",
        "name": "Data Analysis",
        "description": "Statistics, Pandas, hypothesis testing, insights",
        "category": "analysis",
        "icon": "📊",
        "levels": {1: "Descriptive stats", 5: "Predictive modeling", 10: "Causal inference"},
        "prerequisites": ["python", "sql"],
        "tools": ["data_analysis", "chart_creation"],
        "tags": ["data"],
    },
    {
        "id": "problem_solving",
        "name": "Problem Solving",
        "description": "Decompose complex problems, root cause, creative solutions",
        "category": "cognitive",
        "icon": "🧩",
        "levels": {1: "5 Whys", 5: "TRIZ, systems thinking", 10: "Novel framework creation"},
        "prerequisites": [],
        "tools": [],
        "tags": ["thinking"],
    },
    # ─── Creative ────────────────────────────────────────────────────────
    {
        "id": "copywriting",
        "name": "Copywriting",
        "description": "Persuasive copy, brand voice, CTAs, A/B testing",
        "category": "creative",
        "icon": "✍️",
        "levels": {1: "Basic copy", 5: "Conversion optimization", 10: "Brand strategy"},
        "prerequisites": [],
        "tools": ["document_write"],
        "tags": ["marketing"],
    },
    {
        "id": "seo",
        "name": "SEO Optimization",
        "description": "Keyword research, on-page, technical SEO, link building",
        "category": "creative",
        "icon": "🔎",
        "levels": {1: "Meta tags", 5: "Technical audit + content clusters", 10: "Enterprise SEO"},
        "prerequisites": [],
        "tools": ["web_scrape", "data_analysis"],
        "tags": ["marketing"],
    },
    {
        "id": "design_thinking",
        "name": "Design Thinking",
        "description": "Empathize, define, ideate, prototype, test",
        "category": "creative",
        "icon": "🎨",
        "levels": {1: "User interviews", 5: "Journey mapping", 10: "Design system strategy"},
        "prerequisites": [],
        "tools": ["document_write"],
        "tags": ["design"],
    },
    {
        "id": "storytelling",
        "name": "Storytelling",
        "description": "Narrative structure, emotional hooks, brand stories",
        "category": "creative",
        "icon": "📖",
        "levels": {1: "Basic narrative", 5: "Emotional arcs", 10: "Transmedia storytelling"},
        "prerequisites": [],
        "tools": ["document_write"],
        "tags": ["marketing"],
    },
    # ─── Interpersonal ───────────────────────────────────────────────────
    {
        "id": "communication",
        "name": "Communication",
        "description": "Clear, concise, empathetic communication across channels",
        "category": "interpersonal",
        "icon": "💬",
        "levels": {1: "Clear writing", 5: "Persuasion, negotiation", 10: "Crisis comms"},
        "prerequisites": [],
        "tools": ["email", "slack"],
        "tags": ["soft"],
    },
    {
        "id": "empathy",
        "name": "Empathy & Emotional Intelligence",
        "description": "Understand emotions, active listening, de-escalation",
        "category": "interpersonal",
        "icon": "❤️",
        "levels": {1: "Active listening", 5: "Conflict resolution", 10: "Organizational EQ"},
        "prerequisites": [],
        "tools": ["crm"],
        "tags": ["support"],
    },
    {
        "id": "leadership",
        "name": "Leadership & Mentorship",
        "description": "Coaching, delegation, feedback, team motivation",
        "category": "interpersonal",
        "icon": "👑",
        "levels": {1: "1:1 feedback", 5: "Team leadership", 10: "Org transformation"},
        "prerequisites": ["communication"],
        "tools": [],
        "tags": ["management"],
    },
    # ─── Domain ──────────────────────────────────────────────────────────
    {
        "id": "finance",
        "name": "Finance & Accounting",
        "description": "Financial statements, forecasting, budgeting, valuation",
        "category": "domain",
        "icon": "💰",
        "levels": {1: "Basic bookkeeping", 5: "DCF, LBO", 10: "CFO strategy"},
        "prerequisites": ["data_analysis"],
        "tools": ["data_analysis", "chart_creation"],
        "tags": ["finance"],
    },
    {
        "id": "marketing",
        "name": "Digital Marketing",
        "description": "Funnels, attribution, growth loops, performance marketing",
        "category": "domain",
        "icon": "📣",
        "levels": {1: "Basic campaigns", 5: "Growth hacking", 10: "CMO strategy"},
        "prerequisites": ["data_analysis", "copywriting"],
        "tools": ["data_analysis", "document_write"],
        "tags": ["marketing"],
    },
    {
        "id": "sales",
        "name": "Sales & Lead Qualification",
        "description": "BANT, SPICED, objection handling, closing",
        "category": "domain",
        "icon": "💼",
        "levels": {1: "Qualification", 5: "Complex sales", 10: "Enterprise deal strategy"},
        "prerequisites": ["communication"],
        "tools": ["crm", "email"],
        "tags": ["sales"],
    },
    {
        "id": "legal",
        "name": "Legal & Compliance",
        "description": "Contract review, GDPR, SOC2, risk assessment",
        "category": "domain",
        "icon": "⚖️",
        "levels": {1: "Basic contract reading", 5: "Compliance mapping", 10: "Legal strategy"},
        "prerequisites": [],
        "tools": ["document_read", "document_write"],
        "tags": ["legal"],
    },
    {
        "id": "hr",
        "name": "HR & Recruiting",
        "description": "Sourcing, screening, interviewing, onboarding",
        "category": "domain",
        "icon": "👥",
        "levels": {1: "Resume screening", 5: "Interview design", 10: "Talent strategy"},
        "prerequisites": ["communication"],
        "tools": ["document_read", "crm"],
        "tags": ["hr"],
    },
    # ─── Automation ──────────────────────────────────────────────────────
    {
        "id": "workflow_automation",
        "name": "Workflow Automation",
        "description": "Zapier, Make, n8n, RPA, process mining",
        "category": "automation",
        "icon": "⚙️",
        "levels": {1: "Basic zaps", 5: "Complex multi-app automations", 10: "Process mining"},
        "prerequisites": ["api_integration"],
        "tools": ["api_call", "file_system"],
        "tags": ["automation"],
    },
    {
        "id": "rpa",
        "name": "RPA (Robotic Process Automation)",
        "description": "Automate repetitive tasks, screen scraping, data entry",
        "category": "automation",
        "icon": "🤖",
        "levels": {1: "Record & replay", 5: "Intelligent RPA", 10: "Hyperautomation"},
        "prerequisites": ["workflow_automation"],
        "tools": ["file_system", "api_call"],
        "tags": ["automation"],
    },
    # ─── Analysis ────────────────────────────────────────────────────────
    {
        "id": "market_research",
        "name": "Market Research",
        "description": "TAM/SAM/SOM, competitor analysis, trends, SWOT",
        "category": "analysis",
        "icon": "📈",
        "levels": {1: "Basic competitor list", 5: "TAM modeling + SWOT", 10: "Disruptive trend prediction"},
        "prerequisites": ["research", "data_analysis"],
        "tools": ["web_search", "data_analysis"],
        "tags": ["research"],
    },
    {
        "id": "risk_assessment",
        "name": "Risk Assessment",
        "description": "Identify, quantify, mitigate risks, risk matrix",
        "category": "analysis",
        "icon": "⚠️",
        "levels": {1: "Risk list", 5: "Quantified risk matrix", 10: "Monte Carlo"},
        "prerequisites": ["critical_thinking"],
        "tools": ["data_analysis", "document_write"],
        "tags": ["risk"],
    },
    # ─── Communication ───────────────────────────────────────────────────
    {
        "id": "email_management",
        "name": "Email Management",
        "description": "Triage, prioritize, draft, summarize emails",
        "category": "communication",
        "icon": "📧",
        "levels": {1: "Basic triage", 5: "Context-aware drafting", 10: "Inbox zero system"},
        "prerequisites": ["communication"],
        "tools": ["email", "document_read"],
        "tags": ["productivity"],
    },
    {
        "id": "meeting_facilitation",
        "name": "Meeting Facilitation",
        "description": "Agenda, facilitation, notes, action items, follow-up",
        "category": "communication",
        "icon": "📅",
        "levels": {1: "Agenda + notes", 5: "Conflict facilitation", 10: "High-stakes facilitation"},
        "prerequisites": ["communication"],
        "tools": ["document_write", "api_call"],
        "tags": ["productivity"],
    },
    # ─── Additional Technical ────────────────────────────────────────────
    {
        "id": "machine_learning",
        "name": "Machine Learning",
        "description": "Supervised/unsupervised, feature engineering, model eval",
        "category": "technical",
        "icon": "🤖",
        "levels": {1: "Linear models", 5: "Deep learning", 10: "Research SOTA"},
        "prerequisites": ["python", "data_analysis"],
        "tools": ["code_execution", "data_analysis"],
        "tags": ["ai"],
    },
    {
        "id": "nlp",
        "name": "NLP & LLM",
        "description": "Prompt engineering, RAG, fine-tuning, evaluation",
        "category": "technical",
        "icon": "💬",
        "levels": {1: "Prompt basics", 5: "RAG + fine-tune", 10: "LLM research"},
        "prerequisites": ["machine_learning"],
        "tools": ["document_write", "data_analysis"],
        "tags": ["ai"],
    },
    {
        "id": "data_engineering",
        "name": "Data Engineering",
        "description": "ETL, pipelines, warehouses, Airflow, dbt",
        "category": "technical",
        "icon": "🔧",
        "levels": {1: "Basic ETL", 5: "Airflow + dbt", 10: "Petabyte pipelines"},
        "prerequisites": ["python", "sql"],
        "tools": ["database", "file_system"],
        "tags": ["data"],
    },
    {
        "id": "cloud_architecture",
        "name": "Cloud Architecture",
        "description": "AWS/GCP/Azure, IaC, cost optimization, resilience",
        "category": "technical",
        "icon": "☁️",
        "levels": {1: "EC2/S3 basics", 5: "Multi-region + IaC", 10: "Cloud economics at scale"},
        "prerequisites": ["devops"],
        "tools": ["api_call", "file_system"],
        "tags": ["cloud"],
    },
    # ─── More Domain ─────────────────────────────────────────────────────
    {
        "id": "customer_success",
        "name": "Customer Success",
        "description": "Onboarding, adoption, churn prevention, expansion",
        "category": "domain",
        "icon": "🎓",
        "levels": {1: "Onboarding checklists", 5: "Health scores + playbooks", 10: "CS org design"},
        "prerequisites": ["empathy", "data_analysis"],
        "tools": ["crm", "email"],
        "tags": ["customer"],
    },
    {
        "id": "product_management",
        "name": "Product Management",
        "description": "PRDs, prioritization (RICE), metrics, roadmaps",
        "category": "domain",
        "icon": "📦",
        "levels": {1: "User stories", 5: "RICE + roadmaps", 10: "Product org leadership"},
        "prerequisites": ["critical_thinking", "data_analysis"],
        "tools": ["document_write", "data_analysis"],
        "tags": ["product"],
    },
    {
        "id": "qa_testing",
        "name": "QA & Testing",
        "description": "Test planning, automation, bug triage, coverage",
        "category": "technical",
        "icon": "🧪",
        "levels": {1: "Manual testing", 5: "Automation + coverage", 10: "Chaos engineering"},
        "prerequisites": [],
        "tools": ["code_execution", "file_system"],
        "tags": ["quality"],
    },
    {
        "id": "translation",
        "name": "Translation & Localization",
        "description": "50+ languages, tone preservation, glossary, cultural adaptation",
        "category": "communication",
        "icon": "🌐",
        "levels": {1: "Basic translation", 5: "Localization + QA", 10: "Transcreation"},
        "prerequisites": [],
        "tools": ["document_read", "document_write"],
        "tags": ["localization"],
    },
    # ─── Additional 24 skills to reach 60+ ─────────────────────────────────
    {
        "id": "negotiation",
        "name": "Negotiation",
        "description": "BATNA, ZOPA, win-win, high-stakes negotiation tactics",
        "category": "interpersonal",
        "icon": "🤝",
        "levels": {1: "Basic BATNA", 5: "High-stakes deals", 10: "Diplomatic negotiation"},
        "prerequisites": ["communication", "empathy"],
        "tools": ["document_read"],
        "tags": ["sales", "leadership"],
    },
    {
        "id": "public_speaking",
        "name": "Public Speaking",
        "description": "Keynotes, storytelling, audience engagement, slide design",
        "category": "communication",
        "icon": "🎤",
        "levels": {1: "Clear delivery", 5: "Persuasive keynotes", 10: "TED-level"},
        "prerequisites": ["communication", "storytelling"],
        "tools": ["document_write"],
        "tags": ["communication"],
    },
    {
        "id": "time_management",
        "name": "Time Management",
        "description": "Prioritization, Eisenhower matrix, time blocking, deep work",
        "category": "cognitive",
        "icon": "⏰",
        "levels": {1: "Todo lists", 5: "Time blocking + deep work", 10: "Org-wide productivity"},
        "prerequisites": [],
        "tools": ["document_write"],
        "tags": ["productivity"],
    },
    {
        "id": "project_management",
        "name": "Project Management",
        "description": "Agile, Scrum, Kanban, Gantt, risk tracking, stakeholder mgmt",
        "category": "domain",
        "icon": "📋",
        "levels": {1: "Kanban basics", 5: "Scrum master + metrics", 10: "Program management"},
        "prerequisites": ["communication", "leadership"],
        "tools": ["api_call", "document_write"],
        "tags": ["management"],
    },
    {
        "id": "ux_design",
        "name": "UX/UI Design",
        "description": "Wireframes, prototypes, user research, Figma, accessibility",
        "category": "creative",
        "icon": "🎨",
        "levels": {1: "Wireframes", 5: "Design systems", 10: "Design org leadership"},
        "prerequisites": ["design_thinking"],
        "tools": ["document_write", "image_generation"],
        "tags": ["design"],
    },
    {
        "id": "video_editing",
        "name": "Video Editing",
        "description": "Storyboarding, editing, color grading, motion graphics",
        "category": "creative",
        "icon": "🎬",
        "levels": {1: "Basic cuts", 5: "Advanced editing + motion", 10: "Cinematic directing"},
        "prerequisites": [],
        "tools": ["document_write"],
        "tags": ["creative"],
    },
    {
        "id": "prompt_engineering",
        "name": "Prompt Engineering",
        "description": "Chain-of-thought, few-shot, RAG, prompt optimization, evaluation",
        "category": "technical",
        "icon": "💡",
        "levels": {1: "Basic prompts", 5: "Advanced CoT + RAG", 10: "LLM eval framework"},
        "prerequisites": ["nlp"],
        "tools": ["document_write", "data_analysis"],
        "tags": ["ai"],
    },
    {
        "id": "blockchain",
        "name": "Blockchain & Web3",
        "description": "Smart contracts, DeFi, tokenomics, Solidity, auditing",
        "category": "technical",
        "icon": "⛓️",
        "levels": {1: "Wallet + basics", 5: "Smart contracts + DeFi", 10: "Protocol design"},
        "prerequisites": ["security", "python"],
        "tools": ["code_execution", "file_system"],
        "tags": ["web3"],
    },
    {
        "id": "data_visualization",
        "name": "Data Visualization",
        "description": "Charts, dashboards, D3, Tableau, storytelling with data",
        "category": "analysis",
        "icon": "📈",
        "levels": {1: "Bar/line charts", 5: "Interactive dashboards", 10: "Data art + VR"},
        "prerequisites": ["data_analysis"],
        "tools": ["chart_creation", "data_analysis"],
        "tags": ["data"],
    },
    {
        "id": "customer_journey",
        "name": "Customer Journey Mapping",
        "description": "Touchpoints, pain points, moments of truth, service blueprint",
        "category": "domain",
        "icon": "🗺️",
        "levels": {1: "Basic journey", 5: "Service blueprint", 10: "Ecosystem mapping"},
        "prerequisites": ["empathy", "design_thinking"],
        "tools": ["document_write"],
        "tags": ["customer"],
    },
    {
        "id": "growth_hacking",
        "name": "Growth Hacking",
        "description": "AARRR, viral loops, referral programs, experiments",
        "category": "domain",
        "icon": "🚀",
        "levels": {1: "AARRR basics", 5: "Viral loop design", 10: "Growth org"},
        "prerequisites": ["marketing", "data_analysis"],
        "tools": ["data_analysis", "api_call"],
        "tags": ["growth"],
    },
    {
        "id": "content_strategy",
        "name": "Content Strategy",
        "description": "Content pillars, calendars, governance, repurposing",
        "category": "creative",
        "icon": "🗂️",
        "levels": {1: "Content calendar", 5: "Pillar strategy", 10: "Content org"},
        "prerequisites": ["copywriting", "seo"],
        "tools": ["document_write"],
        "tags": ["content"],
    },
    {
        "id": "email_marketing",
        "name": "Email Marketing",
        "description": "Segmentation, automation, deliverability, copy, A/B testing",
        "category": "domain",
        "icon": "📧",
        "levels": {1: "Basic campaigns", 5: "Automation + segmentation", 10: "Lifecycle marketing"},
        "prerequisites": ["copywriting"],
        "tools": ["email", "data_analysis"],
        "tags": ["marketing"],
    },
    {
        "id": "social_listening",
        "name": "Social Listening",
        "description": "Monitor brand mentions, sentiment, trends, crisis detection",
        "category": "analysis",
        "icon": "👂",
        "levels": {1: "Manual monitoring", 5: "Sentiment + trends", 10: "Predictive social"},
        "prerequisites": ["data_analysis"],
        "tools": ["web_search", "data_analysis"],
        "tags": ["social"],
    },
    {
        "id": "competitive_intelligence",
        "name": "Competitive Intelligence",
        "description": "Track competitors, pricing, features, win/loss analysis",
        "category": "analysis",
        "icon": "🕵️",
        "levels": {1: "Competitor list", 5: "Win/loss + pricing", 10: "War gaming"},
        "prerequisites": ["market_research"],
        "tools": ["web_search", "data_analysis"],
        "tags": ["competitive"],
    },
    {
        "id": "financial_modeling",
        "name": "Financial Modeling",
        "description": "3-statement, DCF, LBO, comps, scenario analysis",
        "category": "domain",
        "icon": "📉",
        "levels": {1: "Basic P&L", 5: "LBO + DCF", 10: "Complex derivatives"},
        "prerequisites": ["finance", "data_analysis"],
        "tools": ["data_analysis", "chart_creation"],
        "tags": ["finance"],
    },
    {
        "id": "hr_analytics",
        "name": "HR Analytics",
        "description": "Attrition prediction, engagement, DEI metrics, workforce planning",
        "category": "domain",
        "icon": "📊",
        "levels": {1: "Basic HR reports", 5: "Predictive attrition", 10: "Workforce strategy"},
        "prerequisites": ["data_analysis", "hr"],
        "tools": ["data_analysis", "chart_creation"],
        "tags": ["hr", "analytics"],
    },
    {
        "id": "legal_research",
        "name": "Legal Research",
        "description": "Case law, statutes, due diligence, memo drafting",
        "category": "domain",
        "icon": "📚",
        "levels": {1: "Basic research", 5: "Memo + due diligence", 10: "Appellate strategy"},
        "prerequisites": ["legal", "research"],
        "tools": ["document_read", "web_search"],
        "tags": ["legal"],
    },
    {
        "id": "incident_response",
        "name": "Incident Response",
        "description": "Triage, containment, eradication, recovery, post-mortem",
        "category": "technical",
        "icon": "🚨",
        "levels": {1: "Basic triage", 5: "Full IR lifecycle", 10: "CSIRT leadership"},
        "prerequisites": ["security", "devops"],
        "tools": ["api_call", "file_system", "slack"],
        "tags": ["security"],
    },
    {
        "id": "threat_modeling",
        "name": "Threat Modeling",
        "description": "STRIDE, attack trees, risk ranking, mitigations",
        "category": "technical",
        "icon": "🎯",
        "levels": {1: "STRIDE basics", 5: "Attack trees + mitigations", 10: "Org threat program"},
        "prerequisites": ["security"],
        "tools": ["document_write", "data_analysis"],
        "tags": ["security"],
    },
    {
        "id": "compliance",
        "name": "Compliance & Governance",
        "description": "SOC2, ISO27001, GDPR, audit prep, evidence collection",
        "category": "domain",
        "icon": "📋",
        "levels": {1: "Checklist basics", 5: "Audit prep", 10: "Governance program"},
        "prerequisites": ["legal"],
        "tools": ["document_write", "file_system"],
        "tags": ["compliance"],
    },
    {
        "id": "knowledge_management",
        "name": "Knowledge Management",
        "description": "KB architecture, tagging, search, curation, RAG",
        "category": "cognitive",
        "icon": "📚",
        "levels": {1: "Basic KB", 5: "RAG + curation", 10: "Org knowledge graph"},
        "prerequisites": ["research"],
        "tools": ["document_read", "document_write"],
        "tags": ["knowledge"],
    },
    {
        "id": "change_management",
        "name": "Change Management",
        "description": "ADKAR, stakeholder analysis, communication plans, adoption metrics",
        "category": "domain",
        "icon": "🔄",
        "levels": {1: "Stakeholder map", 5: "ADKAR + metrics", 10: "Transformation leadership"},
        "prerequisites": ["leadership", "communication"],
        "tools": ["document_write"],
        "tags": ["management"],
    },
    {
        "id": "coaching",
        "name": "Coaching & Mentorship",
        "description": "GROW model, active listening, powerful questions, accountability",
        "category": "interpersonal",
        "icon": "🧭",
        "levels": {1: "GROW basics", 5: "Systemic coaching", 10: "Coaching culture"},
        "prerequisites": ["empathy", "leadership"],
        "tools": [],
        "tags": ["coaching"],
    },
]


def get_skill(skill_id: str) -> dict | None:
    for s in SKILL_LIBRARY:
        if s["id"] == skill_id:
            return s
    return None


def list_skills(category: str | None = None, search: str | None = None) -> list[dict]:
    skills = SKILL_LIBRARY
    if category:
        skills = [s for s in skills if s["category"] == category]
    if search:
        q = search.lower()
        skills = [
            s for s in skills if q in s["name"].lower() or q in s["description"].lower() or any(q in tag for tag in s.get("tags", []))
        ]
    return skills


def get_skills_for_agent(agent_skills: list[str]) -> list[dict]:
    """Get full skill definitions for a list of skill ids or names."""
    result = []
    for name in agent_skills:
        # Try id first, then name fuzzy
        skill = get_skill(name.lower().replace(" ", "_").replace("-", "_"))
        if not skill:
            # Fuzzy by name
            for s in SKILL_LIBRARY:
                if s["name"].lower() == name.lower() or s["id"] == name.lower():
                    skill = s
                    break
        if skill:
            result.append(skill)
    return result


def recommend_skills(current_skills: list[str], goal: str | None = None) -> list[dict]:
    """Recommend skills based on current skills and goal."""
    current_set = set(s.lower() for s in current_skills)
    recommendations = []

    # If goal provided, find skills related to goal keywords
    if goal:
        goal_lower = goal.lower()
        for skill in SKILL_LIBRARY:
            if skill["id"] in current_set:
                continue
            # Check if skill tags or description matches goal
            if any(word in skill["description"].lower() or word in " ".join(skill.get("tags", [])).lower() for word in goal_lower.split()):
                recommendations.append(skill)

    # Always recommend prerequisites that are missing
    for skill_id in current_skills:
        skill = get_skill(skill_id.lower().replace(" ", "_"))
        if skill and skill.get("prerequisites"):
            for prereq in skill["prerequisites"]:
                if prereq not in current_set:
                    prereq_skill = get_skill(prereq)
                    if prereq_skill and prereq_skill not in recommendations:
                        recommendations.append(prereq_skill)

    # If still less than 5, add popular complementary skills
    if len(recommendations) < 5:
        popular = ["communication", "critical_thinking", "data_analysis", "python", "problem_solving"]
        for pid in popular:
            if pid not in current_set and get_skill(pid) not in recommendations:
                recommendations.append(get_skill(pid))
                if len(recommendations) >= 5:
                    break

    return recommendations[:10]


def calculate_skill_xp_gain(
    current_proficiency: int, task_complexity: int = 1, success: bool = True
) -> int:
    """Calculate XP gain for a skill after a task. Higher proficiency = slower leveling."""
    base = 10 * task_complexity
    if not success:
        base = base // 4
    # Diminishing returns: higher level = less XP
    multiplier = max(0.2, 1.0 - (current_proficiency / 15))
    return int(base * multiplier)


def can_level_up(proficiency: int, xp: int) -> bool:
    """Check if skill can level up based on XP. Simplified leveling curve."""
    # XP needed for next level: level * 100
    needed = proficiency * 100
    return xp >= needed
