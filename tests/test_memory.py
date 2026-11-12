"""Unit tests for target-scoped retrieval (PENTIA 4.0.4).

ChromaDB is an optional dependency and is NOT installed in the test venv,
so these tests drive MemoryStore with a fake in-memory collection and a
fake embeddings provider. They test the where= plumbing, the target
derivation helper, and the RAGPipeline pass-through — not ChromaDB
itself (the real where= behavior is measured separately in the eval
harness, which runs against a real ChromaDB store).
"""
import asyncio

from core.memory import MemoryStore, extract_target


class FakeEmbeddings:
    async def embed_texts(self, texts):
        return [[0.1] * 4 for _ in texts]

    async def embed_text(self, text):
        return [0.1] * 4


class FakeCollection:
    """Minimal stand-in for a ChromaDB collection: stores documents with
    metadata and applies an exact-match `where` filter like ChromaDB."""

    def __init__(self):
        self.documents = []
        self.metadatas = []
        self.last_query_kwargs = None

    def add(self, documents, metadatas, ids, embeddings):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)

    def query(self, **kwargs):
        self.last_query_kwargs = kwargs
        where = kwargs.get("where")
        docs, metas = self.documents, self.metadatas
        if where:
            key, value = next(iter(where.items()))
            docs = [d for d, m in zip(docs, metas) if m.get(key) == value]
            metas = [m for m in metas if m.get(key) == value]
        n = kwargs.get("n_results", len(docs))
        return {"documents": [docs[:n]], "metadatas": [metas[:n]]}


def make_store():
    # MemoryStore() is safe without chromadb (collection stays None);
    # swap in the fakes afterwards.
    store = MemoryStore()
    store.collection = FakeCollection()
    store.embeddings = FakeEmbeddings()
    return store


def seed(store):
    store.collection.add(
        documents=["note A1 about example.local", "note A2 about example.local"],
        metadatas=[{"target": "example.local"}, {"target": "example.local"}],
        ids=["a1", "a2"],
        embeddings=[[0.1] * 4, [0.1] * 4],
    )
    store.collection.add(
        documents=["note B1 about attacker.local"],
        metadatas=[{"target": "attacker.local"}],
        ids=["b1"],
        embeddings=[[0.1] * 4],
    )


# ---------------------------------------------------------------------------
# extract_target()
# ---------------------------------------------------------------------------

def test_extract_target_single_hostname():
    assert extract_target(
        "What is the severity of the CVE-2024-8190 finding on example.local?"
    ) == "example.local"


def test_extract_target_ipv4_with_port():
    assert extract_target("¿Qué hallazgos tienes sobre 127.0.0.1:8080?") == "127.0.0.1"


def test_extract_target_none_when_no_host():
    assert extract_target("What did you find? Summarize everything.") is None
    assert extract_target("") is None


def test_extract_target_none_when_multiple_hosts():
    assert extract_target(
        "Compare the findings on example.local and attacker.local."
    ) is None


def test_extract_target_ignores_versions_and_bare_words():
    # "2.4.62" is a version, "apache" is a bare word: neither is a target.
    assert extract_target("Upgrade Apache to 2.4.62 or later.") is None
    assert extract_target("What did apache find on the scan?") is None


def test_extract_target_repeated_same_host_counts_once():
    assert extract_target(
        "example.local runs Apache. Tell me about example.local again."
    ) == "example.local"


# ---------------------------------------------------------------------------
# MemoryStore.retrieve() / summary() with target
# ---------------------------------------------------------------------------

def test_retrieve_passes_where_filter_to_chromadb():
    store = make_store()
    seed(store)
    asyncio.run(store.retrieve("findings on example.local", k=4, target="example.local"))
    assert store.collection.last_query_kwargs["where"] == {"target": "example.local"}
    assert store.collection.last_query_kwargs["n_results"] == 4


def test_retrieve_without_target_is_unfiltered():
    store = make_store()
    seed(store)
    asyncio.run(store.retrieve("findings", k=4))
    assert "where" not in store.collection.last_query_kwargs


def test_retrieve_target_returns_only_matching_notes():
    store = make_store()
    seed(store)
    items = asyncio.run(store.retrieve("findings", k=4, target="example.local"))
    assert [i["text"] for i in items] == [
        "note A1 about example.local",
        "note A2 about example.local",
    ]
    assert all(i["metadata"]["target"] == "example.local" for i in items)


def test_retrieve_unknown_target_returns_nothing():
    store = make_store()
    seed(store)
    items = asyncio.run(store.retrieve("findings", k=4, target="no-such-host.local"))
    assert items == []


def test_summary_passes_target_through():
    store = make_store()
    seed(store)
    text = asyncio.run(store.summary("findings", target="attacker.local"))
    assert text == "note B1 about attacker.local"


# ---------------------------------------------------------------------------
# RAGPipeline.answer() pass-through + derivation
# ---------------------------------------------------------------------------

class FakeMemory:
    def __init__(self):
        self.last_summary_kwargs = None

    async def summary(self, query, k=4, target=None):
        self.last_summary_kwargs = {"query": query, "k": k, "target": target}
        return "canned context"


class FakeLLM:
    async def generate(self, prompt, context=None):
        return f"answer (context chars: {len(context or '')})"


def test_rag_answer_derives_target_from_question():
    from neural.rag import RAGPipeline

    memory = FakeMemory()
    pipe = RAGPipeline(memory=memory)
    pipe.llm = FakeLLM()
    asyncio.run(pipe.answer(
        "What is the severity of the CVE-2024-8190 finding on example.local?"
    ))
    assert memory.last_summary_kwargs["target"] == "example.local"


def test_rag_answer_explicit_target_wins_over_derivation():
    from neural.rag import RAGPipeline

    memory = FakeMemory()
    pipe = RAGPipeline(memory=memory)
    pipe.llm = FakeLLM()
    asyncio.run(pipe.answer(
        "What is the severity of the finding on example.local?",
        target="other.local",
    ))
    assert memory.last_summary_kwargs["target"] == "other.local"


def test_rag_answer_without_host_is_unfiltered():
    from neural.rag import RAGPipeline

    memory = FakeMemory()
    pipe = RAGPipeline(memory=memory)
    pipe.llm = FakeLLM()
    asyncio.run(pipe.answer("Summarize all findings."))
    assert memory.last_summary_kwargs["target"] is None
