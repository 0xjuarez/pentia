import asyncio
from typing import List, Optional

from core.ai import LLMClient
from core.memory import MemoryStore, extract_target


class RAGPipeline:
    def __init__(self, memory: Optional[MemoryStore] = None):
        self.memory = memory or MemoryStore()
        self.llm = LLMClient()

    async def answer(self, question: str, k: int = 4, target: Optional[str] = None) -> str:
        # Target-scoped retrieval (v4.0.4): an explicit target wins;
        # otherwise derive one from the question — exactly one host named
        # -> filter to it; none or several -> unfiltered, as before.
        if target is None:
            target = extract_target(question)
        context = await self.memory.summary(question, k=k, target=target)
        prompt = f"Use the retrieved context and provide an answer for: {question}"
        return await self.llm.generate(prompt, context=context)

    async def ingest_notes(self, notes: List[str], metadata: dict | None = None):
        for note in notes:
            await self.memory.add_notes(note, metadata=metadata or {})
