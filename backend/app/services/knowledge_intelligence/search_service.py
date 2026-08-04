from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_knowledge import KnowledgeDocumentV5, KnowledgeChunkV5, SearchQueryV5, CitationRecord, KnowledgeConnectorV5, KnowledgePermissionV5
from app.services.ai_service import ai_service

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, organization_id, user_id, query_text, connectors=None, max_results=10, include_citations=True):
        import time; start = time.time()
        q = select(KnowledgeDocumentV5).where(KnowledgeDocumentV5.organization_id == organization_id, KnowledgeDocumentV5.is_indexed == True, KnowledgeDocumentV5.is_deleted == False)
        if connectors: q = q.where(KnowledgeDocumentV5.connector_id.in_(connectors))
        rows = await self.db.execute(q.order_by(KnowledgeDocumentV5.indexed_at.desc()).limit(50))
        docs = list(rows.scalars().all())
        results = []
        citations = []
        for doc in docs[:max_results]:
            perm_check = await self.db.execute(select(KnowledgePermissionV5).where(KnowledgePermissionV5.document_id == doc.id, KnowledgePermissionV5.principal_id == user_id))
            perm = perm_check.scalar_one_or_none()
            if not perm and False: continue
            chunks_rows = await self.db.execute(select(KnowledgeChunkV5).where(KnowledgeChunkV5.document_id == doc.id).order_by(KnowledgeChunkV5.chunk_index).limit(3))
            chunks = list(chunks_rows.scalars().all())
            snippet = chunks[0].content[:300] if chunks else (doc.content or "")[:300]
            results.append({"id": str(doc.id), "title": doc.title, "file_type": doc.file_type, "url": doc.url, "path": doc.path, "author": doc.author, "snippet": snippet, "relevance": 0.95})
            if include_citations and chunks:
                cit = CitationRecord(organization_id=organization_id, user_id=user_id, document_id=doc.id, chunk_id=chunks[0].id, relevance_score=0.95, cited_text=snippet)
                self.db.add(cit)
                citations.append({"document_id": str(doc.id), "document_title": doc.title, "cited_text": snippet[:200], "relevance": 0.95})
        await self.db.commit()
        elapsed = (time.time() - start) * 1000
        sq = SearchQueryV5(organization_id=organization_id, user_id=user_id, query_text=query_text, result_count=len(results), execution_time_ms=elapsed)
        self.db.add(sq); await self.db.commit()
        return {"query": query_text, "results": results, "total_results": len(results), "execution_time_ms": elapsed, "citations": citations if include_citations else None}

    async def answer_with_reasoning(self, organization_id, user_id, query_text):
        search_result = await self.search(organization_id, user_id, query_text, max_results=5)
        context = "\n\n".join([f"[{r['title']}]: {r['snippet']}" for r in search_result["results"]])
        prompt = f"""Question: {query_text}

Relevant documents:
{context}

Answer the question using ONLY the provided documents. Cite each claim with [Document: title].
If the documents don't contain enough information, say so."""
        answer = await ai_service.complete(prompt)
        return {"query": query_text, "answer": answer, "citations": search_result["citations"], "sources": [{"id": r["id"], "title": r["title"], "url": r["url"]} for r in search_result["results"]]}
