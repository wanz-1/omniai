import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class KnowledgeConnectorV5(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_connectors_v5"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    credentials: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    auth_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_interval_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    documents = relationship("KnowledgeDocumentV5", back_populates="connector", cascade="all, delete-orphan")

    def __repr__(self):
        return f"KnowledgeConnectorV5(id={self.id}, name={self.name}, type={self.connector_type})"


class KnowledgeDocumentV5(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_documents_v5"

    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_connectors_v5.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    connector = relationship("KnowledgeConnectorV5", back_populates="documents")
    chunks = relationship("KnowledgeChunkV5", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("KnowledgePermissionV5", back_populates="document", cascade="all, delete-orphan")
    citations = relationship("CitationRecord", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"KnowledgeDocumentV5(id={self.id}, title={self.title})"


class KnowledgeChunkV5(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_chunks_v5"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents_v5.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    document = relationship("KnowledgeDocumentV5", back_populates="chunks")

    def __repr__(self):
        return f"KnowledgeChunkV5(id={self.id}, document_id={self.document_id}, index={self.chunk_index})"


class KnowledgeGraphNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_graph_nodes"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    properties: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    outgoing_edges = relationship("KnowledgeGraphEdge", back_populates="source_node", foreign_keys="KnowledgeGraphEdge.source_node_id", cascade="all, delete-orphan")
    incoming_edges = relationship("KnowledgeGraphEdge", back_populates="target_node", foreign_keys="KnowledgeGraphEdge.target_node_id", cascade="all, delete-orphan")

    def __repr__(self):
        return f"KnowledgeGraphNode(id={self.id}, name={self.name}, type={self.node_type})"


class KnowledgeGraphEdge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_graph_edges"

    source_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False, index=True)
    target_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    properties: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)

    source_node = relationship("KnowledgeGraphNode", back_populates="outgoing_edges", foreign_keys=[source_node_id])
    target_node = relationship("KnowledgeGraphNode", back_populates="incoming_edges", foreign_keys=[target_node_id])

    def __repr__(self):
        return f"KnowledgeGraphEdge(id={self.id}, source={self.source_node_id}, target={self.target_node_id}, type={self.edge_type})"


class KnowledgePermissionV5(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_permissions_v5"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents_v5.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    principal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    permission_level: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    document = relationship("KnowledgeDocumentV5", back_populates="permissions")

    def __repr__(self):
        return f"KnowledgePermissionV5(id={self.id}, doc_id={self.document_id}, level={self.permission_level})"


class SearchQueryV5(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "search_queries_v5"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    citations = relationship("CitationRecord", back_populates="search_query", cascade="all, delete-orphan")

    def __repr__(self):
        return f"SearchQueryV5(id={self.id}, query={self.query_text[:50]})"


class CitationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "citation_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    search_query_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("search_queries_v5.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents_v5.id"), nullable=False, index=True)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_chunks_v5.id"), nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    search_query = relationship("SearchQueryV5", back_populates="citations")
    document = relationship("KnowledgeDocumentV5", back_populates="citations")

    def __repr__(self):
        return f"CitationRecord(id={self.id}, doc_id={self.document_id}, score={self.relevance_score})"
