import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_knowledge import (
    KnowledgeConnectorV5Response, KnowledgeDocumentV5Response,
    KnowledgeGraphNodeResponse, KnowledgeGraphEdgeResponse,
    SearchRequest, SearchResponse, KnowledgeGraphQuery, KnowledgeGraphResponse,
    ConnectSourceRequest, ConnectSourceResponse,
)
from app.services.knowledge_intelligence.connector_base import BaseConnector
from app.services.knowledge_intelligence.indexing_service import IndexingService
from app.services.knowledge_intelligence.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge_intelligence.search_service import SearchService

router = APIRouter()


@router.post("/connectors", response_model=KnowledgeConnectorV5Response)
async def connect_source(req: ConnectSourceRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BaseConnector(db)
    return await svc.create_connector(current_user.organization_id or current_user.id, req.name, req.connector_type, req.credentials, req.config, current_user.id)


@router.get("/connectors", response_model=list[KnowledgeConnectorV5Response])
async def list_connectors(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BaseConnector(db)
    return await svc.list_connectors(current_user.organization_id or current_user.id)


@router.post("/connectors/{connector_id}/sync", response_model=KnowledgeConnectorV5Response)
async def sync_connector(connector_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BaseConnector(db)
    return await svc.sync_connector(connector_id)


@router.delete("/connectors/{connector_id}")
async def disconnect_source(connector_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BaseConnector(db)
    result = await svc.disconnect(connector_id)
    return {"status": "disconnected", "id": str(connector_id)}


@router.post("/documents/index", response_model=KnowledgeDocumentV5Response)
async def index_document(connector_id: uuid.UUID, title: str, content: str | None = None, file_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = IndexingService(db)
    return await svc.index_document(connector_id, current_user.organization_id or current_user.id, title, content, file_type)


@router.get("/documents", response_model=list[KnowledgeDocumentV5Response])
async def list_documents(connector_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = IndexingService(db)
    return await svc.list_documents(current_user.organization_id or current_user.id, connector_id)


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = SearchService(db)
    return await svc.search(current_user.organization_id or current_user.id, current_user.id, req.query, req.connectors, req.max_results, req.include_citations)


@router.post("/query")
async def query_with_reasoning(query: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = SearchService(db)
    return await svc.answer_with_reasoning(current_user.organization_id or current_user.id, current_user.id, query)


@router.post("/graph/query")
async def query_knowledge_graph(req: KnowledgeGraphQuery, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = KnowledgeGraphService(db)
    result = await svc.query_graph(current_user.organization_id or current_user.id, req.query, req.node_types, req.max_depth)
    return {"nodes": result["nodes"], "edges": result["edges"], "explanation": f"Found {len(result['nodes'])} entities and {len(result['edges'])} relationships"}
