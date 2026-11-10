import asyncio
import logging
import uuid
from typing import Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover
    chromadb = None
    Settings = None

# True when the optional chromadb dependency is importable.
AVAILABLE = chromadb is not None

from .embeddings import EmbeddingsProvider

logger = logging.getLogger("pentia.memory")


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
        # The old duckdb+parquet backend setting was removed in
        # newer chromadb versions. PersistentClient is the supported API;
        # fall back to Client(Settings(persist_directory=...)) for older
        # versions. A failure here must not crash construction: the error
        # surfaces only when memory is actually used.
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
        except Exception:
            try:
                self.client = chromadb.Client(Settings(persist_directory=self.persist_dir))
            except Exception as e:
                logger.warning(f"Chromadb no disponible: {e}")
                self.client = None
                return
        try:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.warning(f"No se pudo abrir la colección ChromaDB: {e}")
            self.collection = None

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
            raise RuntimeError(
                "Memoria no disponible: ChromaDB no está instalado o no se pudo "
                "inicializar (dependencia opcional). "
                "Instala las dependencias ML con INSTALL_HEAVY=1 ./install.sh"
            )

        chunks = self.chunk_text(notes)
        # Batch-embed all chunks in one call, then a single collection
        # write. Chunk IDs are uuid5(chunk), so re-ingesting the same text
        # produces duplicate IDs: prefer collection.upsert when available;
        # otherwise fall back to add() and skip duplicate chunks with a
        # warning instead of failing the whole call.
        embeddings = await self.embeddings.embed_texts(chunks)
        metadatas = [metadata or {} for _ in chunks]
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, chunk)) for chunk in chunks]

        upsert = getattr(self.collection, "upsert", None)
        if callable(upsert):
            await asyncio.to_thread(
                upsert, documents=chunks, metadatas=metadatas, ids=ids, embeddings=embeddings
            )
        else:
            try:
                await asyncio.to_thread(
                    self.collection.add, documents=chunks, metadatas=metadatas, ids=ids, embeddings=embeddings
                )
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    for chunk, meta, chunk_id, vector in zip(chunks, metadatas, ids, embeddings):
                        try:
                            await asyncio.to_thread(
                                self.collection.add,
                                documents=[chunk], metadatas=[meta], ids=[chunk_id], embeddings=[vector],
                            )
                        except Exception as chunk_error:
                            logger.warning(f"Skipping already-ingested chunk {chunk_id}: {chunk_error}")
                else:
                    raise
        # PersistentClient auto-persiste; .persist() solo existe en clientes
        # antiguos basados en Settings, así que se llama solo si existe.
        persist = getattr(self.client, "persist", None)
        if callable(persist):
            await asyncio.to_thread(persist)

    async def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        if self.collection is None:
            raise RuntimeError(
                "Memoria no disponible: ChromaDB no está instalado o no se pudo "
                "inicializar (dependencia opcional). "
                "Instala las dependencias ML con INSTALL_HEAVY=1 ./install.sh"
            )

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
