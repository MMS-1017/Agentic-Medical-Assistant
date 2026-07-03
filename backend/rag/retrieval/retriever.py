from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.rag.vectorstore.client import get_qdrant_client


@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def retrieve_medical_context(query: str, k: int = 3) -> list[str]:
    """Return top-k relevant medical text chunks for the given query."""
    model = _get_embedding_model()
    vector = model.encode(query).tolist()
    client = get_qdrant_client()
    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=vector,
        limit=k,
    )
    return [hit.payload["text"] for hit in results]
