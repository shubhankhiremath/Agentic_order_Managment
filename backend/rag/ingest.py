from __future__ import annotations

import os
from pathlib import Path

_DISABLED = {
    "TRANSFORMERS_NO_TF": "1",
    "TRANSFORMERS_NO_FLAX": "1",
    "USE_TF": "0",
    "DISABLE_TELEMETRY": "YES",
}
for _k, _v in _DISABLED.items():
    os.environ.setdefault(_k, _v)
del _k, _v, _DISABLED

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from backend.config import get_settings
from backend.logging_setup import get_logger

logger = get_logger("rag")
COLLECTION = "demo_policies"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _client(persist_path: str | None = None):
    path = persist_path or get_settings().chroma_path
    Path(path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=path)


def _embedding_fn():
    return SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)


def chunk_markdown(text: str, chunk_size: int = 700, overlap: int = 80) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def ingest_knowledge_base(
    knowledge_dir: str | Path | None = None,
    persist_path: str | None = None,
) -> int:
    settings = get_settings()
    source_dir = Path(knowledge_dir or settings.knowledge_base_dir)
    files = sorted(source_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No markdown files in {source_dir}")

    client = _client(persist_path)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []
    for path in files:
        chunks = chunk_markdown(path.read_text(encoding="utf-8"))
        for i, chunk in enumerate(chunks):
            ids.append(f"{path.stem}-{i}")
            documents.append(chunk)
            metadatas.append({"source": path.name, "title": path.stem.replace("_", " ")})

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("rag_ingested chunks=%s files=%s", len(ids), len(files))
    return len(ids)


def retrieve_policies(query: str, k: int = 4, persist_path: str | None = None) -> list[dict]:
    if not (query or "").strip():
        return []
    client = _client(persist_path)
    collection = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embedding_fn(),
    )
    if collection.count() == 0:
        raise RuntimeError("Policy knowledge base is empty. Run RAG ingestion first.")
    result = collection.query(
        query_texts=[query.strip()],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]
    retrieved = []
    seen = set()
    for doc, meta, dist in zip(docs, metas, dists):
        source = (meta or {}).get("source", "unknown")
        retrieved.append(
            {
                "source": source,
                "title": (meta or {}).get("title", source),
                "content": doc,
                "distance": dist,
            }
        )
        seen.add(source)
    return retrieved


def main() -> None:
    n = ingest_knowledge_base()
    print(f"Ingested {n} chunks into ChromaDB")


if __name__ == "__main__":
    main()
