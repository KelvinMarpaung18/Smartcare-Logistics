"""
Skrip Eksperimen Perbandingan Konfigurasi Chunk Size & Overlap.
Mengevaluasi 3 konfigurasi pemotongan teks:
- Konfigurasi A: 200 kata, overlap 30 kata
- Konfigurasi B: 300 kata, overlap 50 kata (Optimal/Default)
- Konfigurasi C: 400 kata, overlap 75 kata
"""

from pathlib import Path
from typing import Dict, Any
import json
import time

from .config import (
    DOCUMENTS_DIR,
    PROCESSED_DIR,
    CHUNKS_DIR,
    MAX_TOKEN_LENGTH,
    CHUNKING_EXPERIMENTS,
)
from .pdf_extractor import PDFExtractor
from .text_cleaner import TextCleaner
from .chunker import RecursiveWordChunker
from .embedding import EmbeddingPipeline


def run_chunking_experiments() -> Dict[str, Any]:
    print("=== MEMULAI EKSPERIMEN PERBANDINGAN CHUNKING ===")
    extractor = PDFExtractor(DOCUMENTS_DIR)
    cleaner = TextCleaner()
    embedding_pipeline = EmbeddingPipeline()

    # 1. Ekstraksi dan pembersihan
    print("Mengekstrak dan membersihkan teks dari 10 dokumen PDF...")
    raw_corpus = extractor.extract_all_documents()
    cleaned_corpus = {}
    for doc_id, pages in raw_corpus.items():
        cleaned_pages = []
        for p in pages:
            clean_text = cleaner.clean_text(p["raw_text"])
            p_copy = dict(p)
            p_copy["clean_text"] = clean_text
            cleaned_pages.append(p_copy)
        cleaned_corpus[doc_id] = cleaned_pages

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    for exp in CHUNKING_EXPERIMENTS:
        name = exp["name"]
        size = exp["chunk_size"]
        overlap = exp["overlap"]
        print(f"\n--- Menguji {name}: Size={size} kata, Overlap={overlap} kata ---")

        chunker = RecursiveWordChunker(chunk_size=size, chunk_overlap=overlap)
        t0 = time.time()
        chunks = chunker.chunk_corpus(cleaned_corpus)
        chunking_time = time.time() - t0

        # Validasi token pada setiap chunk
        token_counts = []
        truncated_count = 0
        for c in chunks:
            tc = embedding_pipeline.count_tokens(c["text"])
            c["metadata"]["token_count"] = tc
            token_counts.append(tc)
            if tc > MAX_TOKEN_LENGTH:
                truncated_count += 1

        avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
        max_tokens = max(token_counts) if token_counts else 0
        min_tokens = min(token_counts) if token_counts else 0

        exp_data = {
            "name": name,
            "chunk_size_words": size,
            "overlap_words": overlap,
            "total_chunks": len(chunks),
            "chunking_time_seconds": round(chunking_time, 2),
            "token_stats": {
                "avg_tokens": round(avg_tokens, 2),
                "max_tokens": max_tokens,
                "min_tokens": min_tokens,
                "max_allowed": MAX_TOKEN_LENGTH,
                "truncated_chunks_count": truncated_count,
                "truncation_risk_percent": round((truncated_count / len(chunks)) * 100, 2) if chunks else 0.0,
            },
        }
        results[name] = exp_data
        print(f"Hasil {name}: Total Chunk = {len(chunks)}, Rata-rata Token = {avg_tokens:.1f}, Max Token = {max_tokens}, Truncated = {truncated_count}")

        # Simpan chunk hasil eksperimen
        with open(CHUNKS_DIR / f"chunks_{size}_{overlap}.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

    # Simpan laporan hasil eksperimen
    output_path = CHUNKS_DIR / "chunking_experiments_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nLaporan eksperimen berhasil disimpan ke: {output_path}")
    return results


if __name__ == "__main__":
    run_chunking_experiments()
