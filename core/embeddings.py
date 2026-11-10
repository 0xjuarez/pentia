import asyncio
from typing import List

try:
    from nomic import embed as nomic_embed
except ImportError:  # pragma: no cover
    nomic_embed = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


class EmbeddingsProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        # Lazy load: SentenceTransformer construction downloads/loads the
        # model at import time otherwise. Construct on first embed call.

    def _ensure_model(self) -> bool:
        """Construct the SentenceTransformer on first use; False if unavailable."""
        if self.model is not None:
            return True
        if SentenceTransformer is None:
            return False
        try:
            self.model = SentenceTransformer(self.model_name)
            return True
        except Exception:
            self.model = None
            return False

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if nomic_embed is not None:
            return await asyncio.to_thread(nomic_embed, texts)

        if self._ensure_model():
            return await asyncio.to_thread(self.model.encode, texts, show_progress_bar=False)

        raise RuntimeError("No embedding backend installed. Install nomic-embed-text or sentence-transformers.")

    async def embed_text(self, text: str) -> List[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]
