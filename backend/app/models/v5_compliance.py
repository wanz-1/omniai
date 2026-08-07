import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Regulation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regulations"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list] = mapped_column(JSONB, default=list)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Regulation {self.name} ({self.jurisdiction})>"


class Policy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    policy_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer, default=1)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Policy {self.name} (v{self.version})>"


class ComplianceCheck(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_checks"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    check_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    scope: Mapped[list] = mapped_column(JSONB, default=list)
    results_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    results: Mapped[list["ComplianceCheckResult"]] = relationship("ComplianceCheckResult", back_populates="check", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ComplianceCheck {self.name} ({self.status})>"


class ComplianceCheckResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_check_results"

    check_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_checks.id", ondelete="CASCADE"))
    item_type: Mapped[str] = mapped_column(String(20))
    item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    finding: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20))
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    check: Mapped["ComplianceCheck"] = relationship("ComplianceCheck", back_populates="results")

    def __repr__(self):
        return f"<ComplianceCheckResult {self.item_type}:{self.status}>"


class AuditRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    audit_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    scope: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20))
    auditor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    findings_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="audit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AuditRecord {self.title} ({self.status})>"


class Finding(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "findings"

    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_records.id", ondelete="CASCADE"), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    finding_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    audit: Mapped["AuditRecord"] = relationship("AuditRecord", back_populates="findings")
    corrective_actions: Mapped[list["CorrectiveAction"]] = relationship("CorrectiveAction", back_populates="finding", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Finding {self.title} ({self.severity})>"


class CorrectiveAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "corrective_actions"

    finding_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    action_plan: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    finding: Mapped["Finding"] = relationship("Finding", back_populates="corrective_actions")

    def __repr__(self):
        return f"<CorrectiveAction {self.title} ({self.status})>"


class RiskScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_scores"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    score_type: Mapped[str] = mapped_column(String(20))
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float, default=100.0)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime)
    assessed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<RiskScore {self.score_type}:{self.score}>"


class ComplianceReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_reports_v5"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict] = mapped_column(JSONB)
    generated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    generated_at: Mapped[datetime] = mapped_column(DateTime)
    period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ComplianceReport {self.title} ({self.report_type})>"


class ApprovalHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approval_histories"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action_type: Mapped[str] = mapped_column(String(40))
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ApprovalHistory {self.action_type}:{self.status}>"


class IndustryCompliancePack(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_compliance_packs"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    industry: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list] = mapped_column(JSONB, default=list)
    policies: Mapped[list] = mapped_column(JSONB, default=list)
    checks: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f"<IndustryCompliancePack {self.name} ({self.industry})>"


class ComplianceDocumentReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_document_reviews"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    document_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20))
    issues: Mapped[list] = mapped_column(JSONB, default=list)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f"<ComplianceDocumentReview {self.title} ({self.review_status})>"


class RegulatoryUpdate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regulatory_updates"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    regulation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    change_type: Mapped[str] = mapped_column(String(20))
    impact: Mapped[str] = mapped_column(String(20))
    affected_areas: Mapped[list] = mapped_column(JSONB, default=list)
    recommended_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<RegulatoryUpdate {self.title} ({self.change_type})>"
