"""
Ingest medical documents into Qdrant.
Usage: python -m backend.rag.ingestion.pipeline --docs-dir ./docs/medical
"""

import argparse
import uuid
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct

from backend.config import settings
from backend.rag.vectorstore.client import get_qdrant_client, ensure_collection

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def ingest_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = _chunk_text(text)
    vectors = _model.encode(chunks, show_progress_bar=False).tolist()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"text": chunk, "source": path.name},
        )
        for chunk, vec in zip(chunks, vectors)
    ]
    client = get_qdrant_client()
    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def ingest_directory(docs_dir: str) -> None:
    ensure_collection()
    total = 0
    for path in Path(docs_dir).rglob("*.txt"):
        n = ingest_file(path)
        print(f"Ingested {n} chunks from {path.name}")
        total += n
    print(f"Total chunks ingested: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", required=True)
    args = parser.parse_args()
    ingest_directory(args.docs_dir)
