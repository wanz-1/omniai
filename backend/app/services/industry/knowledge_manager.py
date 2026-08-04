from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industry_solutions import IndustryKnowledgeBase
from app.services.ai_service import ai_service


class IndustryKnowledgeManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_knowledge(self, industry_id, title, content=None, category=None, tags=None, source=None):
        entry = IndustryKnowledgeBase(
            industry_id=industry_id, title=title, content=content,
            category=category, tags=tags or [], source=source,
        )
        if content:
            embedding = await self._generate_embedding(content)
            entry.embedding = embedding
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def search_knowledge(self, industry_id, query, limit=5):
        rows = await self.db.execute(
            select(IndustryKnowledgeBase)
            .where(IndustryKnowledgeBase.industry_id == industry_id)
            .where(IndustryKnowledgeBase.content.isnot(None))
            .limit(limit)
        )
        return list(rows.scalars().all())

    async def query_with_knowledge(self, industry_id, query_text):
        results = await self.search_knowledge(industry_id, query_text)
        context = "\n\n".join([f"- {r.title}: {r.content[:500]}" for r in results if r.content])
        prompt = f"""You are an industry knowledge assistant. Use the following knowledge base context to answer the query.

Knowledge Context:
{context}

Query: {query_text}

Provide a helpful, accurate response based on the available knowledge."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.3)
        return {
            "response": result.get("content", ""),
            "sources": [{"title": r.title, "category": r.category} for r in results],
        }

    async def get_knowledge_by_category(self, industry_id, category):
        rows = await self.db.execute(
            select(IndustryKnowledgeBase)
            .where(IndustryKnowledgeBase.industry_id == industry_id)
            .where(IndustryKnowledgeBase.category == category)
        )
        return list(rows.scalars().all())

    async def delete_knowledge(self, knowledge_id):
        entry = await self.db.get(IndustryKnowledgeBase, knowledge_id)
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
            return True
        return False

    async def _generate_embedding(self, text):
        try:
            embeddings = await ai_service.embed([text[:8000]])
            return embeddings[0] if embeddings else None
        except Exception:
            return None
