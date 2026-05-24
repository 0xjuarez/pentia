import asyncio
import uuid
from typing import Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover
    chromadb = None

from .embeddings import EmbeddingsProvider


class MemoryStore:
    def __init__(self, persist_dir: str = ".pentia_memory", collection_name: str = "pentia_notes"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embeddings = EmbeddingsProvider()
        self.client = None
        self.collection = None
        if chromadb is not None:
            self._init_chromadb()

    def _init_chromadb(self):
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_dir))
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        if len(text) <= chunk_size:
            return [text.strip()]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    async def add_notes(self, notes: str, metadata: Optional[Dict] = None):
        if self.collection is None:
            raise RuntimeError("Chromadb not available")

        chunks = self.chunk_text(notes)
        docs = []
        metadatas = []
        ids = []
        embeddings = []

        for chunk in chunks:
            vector = await self.embeddings.embed_text(chunk)
            docs.append(chunk)
            metadatas.append(metadata or {})
            ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, chunk)))
            embeddings.append(vector)

        await asyncio.to_thread(self.collection.add, documents=docs, metadatas=metadatas, ids=ids, embeddings=embeddings)
        await asyncio.to_thread(self.client.persist)

    async def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        if self.collection is None:
            raise RuntimeError("Chromadb not available")

        query_vector = await self.embeddings.embed_text(query)
        results = await asyncio.to_thread(self.collection.query, query_embeddings=[query_vector], n_results=k)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        return [
            {"text": text, "metadata": metadata}
            for text, metadata in zip(documents, metadatas)
        ]

    async def summary(self, query: str) -> str:
        items = await self.retrieve(query)
        return "\n\n".join([item["text"] for item in items])

    async def ingest_documents(self, documents: List[Dict[str, str]]):
        for document in documents:
            await self.add_notes(document.get("text", ""), metadata=document.get("metadata", {}))
