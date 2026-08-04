import uuid
from datetime import datetime
from pydantic import BaseModel


class KnowledgeConnectorV5Response(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; name: str
    connector_type: str; auth_status: str; is_active: bool = True
    last_sync_at: datetime | None = None; total_documents: int = 0
    webhook_url: str | None = None
    class Config: from_attributes = True


class KnowledgeDocumentV5Response(BaseModel):
    id: uuid.UUID; connector_id: uuid.UUID; organization_id: uuid.UUID
    title: str; file_type: str | None = None; file_size: int | None = None
    url: str | None = None; path: str | None = None
    author: str | None = None; indexed_at: datetime | None = None
    is_indexed: bool = False; is_deleted: bool = False
    class Config: from_attributes = True


class KnowledgeChunkV5Response(BaseModel):
    id: uuid.UUID; document_id: uuid.UUID; chunk_index: int
    content: str | None = None; token_count: int | None = None
    class Config: from_attributes = True


class KnowledgeGraphNodeResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; node_type: str
    external_id: str | None = None; name: str
    properties: dict | None = None
    class Config: from_attributes = True


class KnowledgeGraphEdgeResponse(BaseModel):
    id: uuid.UUID; source_node_id: uuid.UUID; target_node_id: uuid.UUID
    edge_type: str; properties: dict | None = None
    weight: float | None = None
    class Config: from_attributes = True


class KnowledgePermissionV5Response(BaseModel):
    id: uuid.UUID; document_id: uuid.UUID; organization_id: uuid.UUID
    principal_type: str; principal_id: uuid.UUID; permission_level: str
    class Config: from_attributes = True


class SearchQueryV5Response(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; user_id: uuid.UUID
    query_text: str; filters: dict | None = None
    result_count: int | None = None; execution_time_ms: float | None = None
    created_at: datetime
    class Config: from_attributes = True


class CitationRecordResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; user_id: uuid.UUID
    document_id: uuid.UUID; relevance_score: float | None = None
    cited_text: str | None = None; created_at: datetime
    class Config: from_attributes = True


class SearchRequest(BaseModel):
    query: str
    connectors: list[uuid.UUID] | None = None
    max_results: int = 10
    min_relevance: float = 0.0
    include_citations: bool = True


class SearchResponse(BaseModel):
    query: str
    results: list
    total_results: int
    execution_time_ms: float
    citations: list | None = None


class KnowledgeGraphQuery(BaseModel):
    query: str
    node_types: list[str] | None = None
    max_depth: int = 2


class KnowledgeGraphResponse(BaseModel):
    nodes: list
    edges: list
    explanation: str


class ConnectSourceRequest(BaseModel):
    connector_type: str
    name: str
    credentials: dict
    config: dict | None = None


class ConnectSourceResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str
