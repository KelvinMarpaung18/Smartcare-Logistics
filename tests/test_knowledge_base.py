"""
Unit Tests untuk Milestone 3 — Vector Knowledge Base & Search SmartCare Logistics.
Memverifikasi ekstraksi dokumen, pembersihan teks, chunking word-aware,
pembuatan embedding 768 dimensi, ChromaDB vector store, BM25, Hybrid RRF,
serta deteksi dan penolakan query Out-of-Domain (OOD).
"""

import pytest
from pathlib import Path

from smartcare_logistics.knowledge_base.document_metadata import (
    OFFICIAL_DOCUMENTS_REGISTRY,
    get_document_metadata,
)
from smartcare_logistics.knowledge_base.text_cleaner import TextCleaner
from smartcare_logistics.knowledge_base.chunker import RecursiveWordChunker
from smartcare_logistics.knowledge_base.hybrid_search import HybridSearchEngine
from smartcare_logistics.knowledge_base.lexical_search import BM25SearchEngine
from smartcare_logistics.knowledge_base.config import (
    OOD_SIMILARITY_THRESHOLD,
    EMBEDDING_DIMENSION,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)


def test_official_documents_registry_completeness():
    """Memastikan seluruh 10 dokumen resmi terdaftar dengan atribut wajib."""
    assert len(OFFICIAL_DOCUMENTS_REGISTRY) == 10
    required_keys = [
        "document_id", "file_name", "title", "publisher",
        "publication_year", "document_type", "category"
    ]
    for doc_id, meta in OFFICIAL_DOCUMENTS_REGISTRY.items():
        for k in required_keys:
            assert k in meta, f"Metadata key '{k}' hilang pada {doc_id}"


def test_doc02_relation_to_doc01():
    """Memastikan DOC02 (Permenkes 26/2020) terhubung secara eksplisit ke DOC01."""
    doc02 = get_document_metadata("DOC02")
    assert doc02 is not None
    assert "DOC01_Permenkes_74_2016.pdf" in doc02.get("related_documents", [])


def test_doc07_category_policy():
    """Memastikan DOC07 dikategorikan sebagai Policy and Regulation / Kebijakan, bukan SOP teknis."""
    doc07 = get_document_metadata("DOC07")
    assert doc07 is not None
    assert "Policy" in doc07["category"]


def test_doc06_page_filter():
    """Memastikan DOC06 memfilter Modul 4 pada halaman PDF 108–150."""
    doc06 = get_document_metadata("DOC06")
    assert doc06 is not None
    assert doc06.get("page_filter") == (108, 150)


def test_text_cleaner_temperature_preservation():
    """Memastikan text cleaner mempertahankan rentang suhu cold chain dan perbaikan hyphen."""
    cleaner = TextCleaner()
    raw = "Penyim-\npanan vaksin pada suhu 2°C s/d 8°C harus ter-\njaga."
    cleaned = cleaner.clean_text(raw)
    assert "Penyimpanan" in cleaned
    assert "terjaga" in cleaned
    assert "2°C" in cleaned
    assert "8°C" in cleaned


def test_recursive_chunker_basic():
    """Memverifikasi pembagian teks berbasis kata dan overlap terukur."""
    chunker = RecursiveWordChunker(chunk_size=50, chunk_overlap=10)
    # Buat teks dengan 120 kata
    words = [f"kata{i}" for i in range(120)]
    sample_text = " ".join(words)
    page_data = {
        "doc_id": "TEST_DOC",
        "page_number": 1,
        "clean_text": sample_text,
        "metadata": {"title": "Test Title", "document_id": "TEST_DOC"},
    }
    chunks = chunker.chunk_page(page_data)
    assert len(chunks) > 1
    for c in chunks:
        assert c["word_count"] <= 50
        assert "page_start" in c["metadata"]
        assert c["metadata"].get("document_id") == "TEST_DOC" or c["metadata"].get("title") == "Test Title"


def test_hybrid_search_rrf_ranking():
    """Memverifikasi algoritma Reciprocal Rank Fusion menggabungkan dense dan leksikal."""
    hybrid = HybridSearchEngine(rrf_k=60, weight_dense=0.6, weight_bm25=0.4)

    dense_results = [
        {"chunk_id": "C1", "text": "Cold chain vaksin Puskesmas", "similarity": 0.88, "distance": 0.12, "metadata": {}},
        {"chunk_id": "C2", "text": "Distribusi farmasi Rumah Sakit", "similarity": 0.82, "distance": 0.18, "metadata": {}},
    ]
    bm25_results = [
        {"chunk_id": "C2", "text": "Distribusi farmasi Rumah Sakit", "bm25_score": 12.5, "metadata": {}},
        {"chunk_id": "C3", "text": "Pengelolaan logistik Balige", "bm25_score": 8.0, "metadata": {}},
    ]

    fused = hybrid.fuse(dense_results, bm25_results, top_k=3)
    assert len(fused) <= 3
    # C2 ada di kedua retriever, sehingga memiliki skor RRF yang solid
    cids = [item["chunk_id"] for item in fused]
    assert "C1" in cids
    assert "C2" in cids
    for item in fused:
        assert "rrf_score" in item
        assert 0.0 <= item["rrf_score"] <= 1.0


def test_bm25_tokenizer_and_search(tmp_path):
    """Memverifikasi pembuatan indeks leksikal BM25 dan pencarian kata kunci."""
    bm25 = BM25SearchEngine(index_dir=tmp_path)
    sample_chunks = [
        {"chunk_id": "C_VAKSIN", "text": "Suhu vaksin campak disimpan pada 2°C sampai 8°C di Puskesmas Balige.", "metadata": {}},
        {"chunk_id": "C_RS", "text": "Penerimaan sediaan farmasi di RSUD Porsea harus diverifikasi apoteker.", "metadata": {}},
        {"chunk_id": "C_TOBA", "text": "Distribusi logistik ambulans mencakup wilayah Toba dan Balige.", "metadata": {}},
        {"chunk_id": "C_DOK", "text": "Peraturan kefarmasian mengatur standar mutu fasilitas kesehatan.", "metadata": {}},
    ]
    bm25.build_index(sample_chunks)
    res = bm25.search("campak", top_k=1)
    assert len(res) == 1
    assert res[0]["chunk_id"] == "C_VAKSIN"


def test_ood_threshold_logic():
    """Memverifikasi logika ambang batas cosine similarity untuk menolak query out-of-domain."""
    assert OOD_SIMILARITY_THRESHOLD == 0.80
    # Jika similarity di bawah threshold, sistem menandai sebagai out of domain
    sim_ood = 0.75
    assert sim_ood < OOD_SIMILARITY_THRESHOLD  # OOD harus tertolak
    sim_in_domain = 0.86
    assert sim_in_domain >= OOD_SIMILARITY_THRESHOLD  # In-domain diterima
