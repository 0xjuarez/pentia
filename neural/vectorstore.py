from typing import List, Optional

from core.memory import MemoryStore


class VectorStore:
    def __init__(self, persist_dir: str = ".pentia_memory", collection_name: str = "pentia_notes"):
        self.memory = MemoryStore(persist_dir=persist_dir, collection_name=collection_name)

    async def index(self, docs: List[str], metadata: Optional[dict] = None):
        for doc in docs:
            await self.memory.add_notes(doc, metadata=metadata or {})

    async def query(self, query_text: str, k: int = 4):
        return await self.memory.retrieve(query_text, k=k)
