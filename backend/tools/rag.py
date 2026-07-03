from langchain_core.tools import tool

from backend.rag.retrieval.retriever import retrieve_medical_context


@tool
def search_medical_knowledge(query: str) -> str:
    """
    Search the medical knowledge base for information relevant to the patient's symptoms.
    Returns up to 3 relevant text excerpts.
    """
    chunks = retrieve_medical_context(query, k=3)
    if not chunks:
        return "No relevant medical information found."
    return "\n\n---\n\n".join(chunks)
