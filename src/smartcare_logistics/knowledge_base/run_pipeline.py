"""
Skrip Eksekusi Penuh Pipeline Ingestion & Indexing Milestone 3.
Memproses seluruh 10 dokumen PDF, melakukan chunking optimal,
menghasilkan vektor embedding E5, mengisi ChromaDB, dan membangun indeks BM25.
"""

from .pipeline import KnowledgeBasePipeline
from .config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


def main():
    print("=== SMARTCARE LOGISTICS - MILESTONE 3 PIPELINE RUNNER ===")
    pipeline = KnowledgeBasePipeline(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )
    stats = pipeline.run_full_pipeline()
    print("\nStatistik Penyelesaian Pipeline:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()
