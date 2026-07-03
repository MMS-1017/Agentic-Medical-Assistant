"""
One-shot project setup script.
1. Creates DB tables
2. Seeds all databases
3. Ingests medical knowledge docs into Qdrant

Run: python scripts/setup.py
"""

import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("=" * 60)
    print("Agentic Medical Assistant — Project Setup")
    print("=" * 60)

    # 1. Seed all databases
    print("\n[1/2] Seeding databases...")
    from backend.database.seed import run_seed
    run_seed()

    # 2. Ingest medical knowledge into Qdrant
    print("\n[2/2] Ingesting medical knowledge into Qdrant RAG...")
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "medical")
    if not os.path.exists(docs_dir):
        print(f"  WARNING: docs/medical not found at {docs_dir} — skipping RAG ingestion.")
    else:
        try:
            from backend.rag.vectorstore.client import ensure_collection
            from backend.rag.ingestion.pipeline import ingest_directory
            ensure_collection()
            ingest_directory(docs_dir)
        except Exception as exc:
            print(f"  WARNING: RAG ingestion failed ({exc}). Is Qdrant running?")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nTest accounts (all use password: Password123!):")
    print("  ahmed.m@example.com     — normal patient, 150 loyalty pts")
    print("  fatima.ali@example.com  — HIGH-RISK cardiac patient, 350 pts")
    print("  omar.k@example.com      — hypertension patient, 50 pts")
    print("  nour.h@example.com      — healthy patient, pending HITL case")
    print("  yasmine.i@example.com   — asthma patient, 500 pts (free consultation)")
    print("\nStart the server:")
    print("  uvicorn backend.app:app --reload")
    print("\nAPI docs: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
