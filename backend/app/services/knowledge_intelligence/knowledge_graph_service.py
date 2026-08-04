from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_knowledge import KnowledgeGraphNode, KnowledgeGraphEdge

class KnowledgeGraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_node(self, organization_id, node_type, external_id, name, properties=None):
        existing = await self.db.execute(select(KnowledgeGraphNode).where(KnowledgeGraphNode.organization_id == organization_id, KnowledgeGraphNode.external_id == external_id, KnowledgeGraphNode.node_type == node_type))
        if existing.scalar_one_or_none(): return existing.scalar_one()
        node = KnowledgeGraphNode(organization_id=organization_id, node_type=node_type, external_id=external_id, name=name, properties=properties or {})
        self.db.add(node); await self.db.commit(); await self.db.refresh(node); return node

    async def add_edge(self, source_node_id, target_node_id, edge_type, properties=None, weight=1.0):
        edge = KnowledgeGraphEdge(source_node_id=source_node_id, target_node_id=target_node_id, edge_type=edge_type, properties=properties or {}, weight=weight)
        self.db.add(edge); await self.db.commit(); await self.db.refresh(edge); return edge

    async def query_graph(self, organization_id, query_text=None, node_types=None, max_depth=2):
        q = select(KnowledgeGraphNode).where(KnowledgeGraphNode.organization_id == organization_id)
        if node_types: q = q.where(KnowledgeGraphNode.node_type.in_(node_types))
        if query_text: q = q.where(KnowledgeGraphNode.name.ilike(f"%{query_text}%"))
        rows = await self.db.execute(q.limit(50))
        nodes = list(rows.scalars().all())
        edge_q = select(KnowledgeGraphEdge).where(or_(KnowledgeGraphEdge.source_node_id.in_([n.id for n in nodes]), KnowledgeGraphEdge.target_node_id.in_([n.id for n in nodes])))
        edge_rows = await self.db.execute(edge_q)
        edges = list(edge_rows.scalars().all())
        return {"nodes": nodes, "edges": edges}
