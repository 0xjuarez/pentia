import asyncio
from typing import List, Optional

from core.ai import LLMClient
from core.memory import MemoryStore


class RAGPipeline:
    def __init__(self, memory: Optional[MemoryStore] = None):
        self.memory = memory or MemoryStore()
        self.llm = LLMClient()

    async def answer(self, question: str) -> str:
        context = await self.memory.summary(question)
        prompt = f"Use the retrieved context and provide an answer for: {question}"
        return await self.llm.generate(prompt, context=context)

    async def ingest_notes(self, notes: List[str], metadata: dict | None = None):
        for note in notes:
            await self.memory.add_notes(note, metadata=metadata or {})
