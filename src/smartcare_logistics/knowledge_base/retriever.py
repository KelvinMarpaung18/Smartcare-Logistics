"""
Modul Unified Knowledge Base Retriever.
Menyediakan antarmuka pencarian terpadu (Dense, BM25, Hybrid RRF),
lengkap dengan deteksi dan penanganan query ambigu serta Out-of-Domain (OOD).
"""

from typing import List, Dict, Any, Optional
import time

from .config import (
    OOD_DISTANCE_THRESHOLD,
    OOD_SIMILARITY_THRESHOLD,
    DEFAULT_TOP_K,
)
from .embedding import EmbeddingPipeline
from .vector_store import ChromaVectorStore
from .lexical_search import BM25SearchEngine
from .hybrid_search import HybridSearchEngine


class KnowledgeBaseRetriever:
    """
    Search engine terpadu untuk Enterprise Knowledge Base SmartCare Logistics.
    """

    def __init__(
        self,
        embedding_pipeline: Optional[EmbeddingPipeline] = None,
        vector_store: Optional[ChromaVectorStore] = None,
        bm25_engine: Optional[BM25SearchEngine] = None,
        hybrid_engine: Optional[HybridSearchEngine] = None,
        ood_similarity_threshold: float = OOD_SIMILARITY_THRESHOLD,
    ):
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_engine = bm25_engine or BM25SearchEngine()
        self.hybrid_engine = hybrid_engine or HybridSearchEngine()
        self.ood_similarity_threshold = ood_similarity_threshold

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = DEFAULT_TOP_K,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Mengeksekusi pencarian pada basis pengetahuan.

        Args:
            query: Teks pertanyaan atau kebutuhan logistik/regulasi.
            mode: 'hybrid' (RRF), 'dense' (ChromaDB), atau 'bm25' (lexical).
            top_k: Jumlah dokumen/chunk teratas yang diambil.
            where_filter: Metadata filtering ChromaDB (opsional).

        Returns:
            Dictionary hasil pencarian berisi:
                - query: Teks query asli
                - mode: Mode pencarian yang digunakan
                - is_out_of_domain: Boolean apakah query di luar domain
                - warning: Catatan atau penjelasan jika query OOD/ambigu
                - latency_ms: Waktu pemrosesan dalam milidetik
                - results: List of top chunk results
        """
        start_time = time.time()
        query_clean = query.strip()
        if not query_clean:
            return {
                "query": query,
                "mode": mode,
                "is_out_of_domain": True,
                "warning": "Query kosong tidak dapat diproses.",
                "latency_ms": 0.0,
                "results": [],
            }

        # 1. Jalankan Dense Retrieval
        query_embedding = self.embedding_pipeline.embed_query(query_clean)
        # Ambil top_k kandidat lebih banyak untuk fusion (misal top 20)
        candidate_k = max(top_k * 3, 20)
        dense_results = self.vector_store.query_similarity(
            query_embedding=query_embedding,
            top_k=candidate_k,
            where_filter=where_filter,
        )

        # 2. Periksa Out-of-Domain (OOD) berdasarkan batas cosine similarity dense vector
        top_dense_sim = dense_results[0]["similarity"] if dense_results else 0.0
        top_dense_dist = dense_results[0]["distance"] if dense_results else 1.0

        is_ood = top_dense_sim < self.ood_similarity_threshold
        warning_msg = None
        if is_ood:
            warning_msg = (
                f"Query terdeteksi di luar cakupan domain korpus logistik kesehatan "
                f"(Cosine Similarity tertinggi: {top_dense_sim:.4f} < ambang batas {self.ood_similarity_threshold:.4f}). "
                f"Informasi yang relevan tidak ditemukan dalam korpus regulasi resmi."
            )

        # 3. Jalankan pencarian sesuai mode yang dipilih
        final_results: List[Dict[str, Any]] = []

        if mode == "dense":
            final_results = dense_results[:top_k]
        elif mode == "bm25":
            final_results = self.bm25_engine.search(query_clean, top_k=top_k)
        elif mode == "hybrid":
            bm25_candidates = self.bm25_engine.search(query_clean, top_k=candidate_k)
            final_results = self.hybrid_engine.fuse(
                dense_results=dense_results,
                bm25_results=bm25_candidates,
                top_k=top_k,
            )
        else:
            raise ValueError(f"Mode pencarian '{mode}' tidak dikenal. Pilih 'hybrid', 'dense', atau 'bm25'.")

        latency_ms = (time.time() - start_time) * 1000.0

        return {
            "query": query,
            "mode": mode,
            "is_out_of_domain": is_ood,
            "warning": warning_msg,
            "top_similarity": float(top_dense_sim),
            "top_distance": float(top_dense_dist),
            "latency_ms": round(latency_ms, 2),
            "total_results": len(final_results),
            "results": final_results,
        }
