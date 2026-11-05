"""
Modul Hybrid Search dengan Reciprocal Rank Fusion (RRF).
Menggabungkan keunggulan Dense Vector Retrieval (semantic understanding)
dan BM25 Lexical Retrieval (exact keyword & regulation clause matching).
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from .config import RRF_K, WEIGHT_DENSE, WEIGHT_BM25


class HybridSearchEngine:
    """
    Mesin pencari hibrida berbasis Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        rrf_k: int = RRF_K,
        weight_dense: float = WEIGHT_DENSE,
        weight_bm25: float = WEIGHT_BM25,
    ):
        self.rrf_k = rrf_k
        self.weight_dense = weight_dense
        self.weight_bm25 = weight_bm25

    def fuse(
        self,
        dense_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Menggabungkan peringkat hasil dense retrieval dan leksikal BM25 menggunakan RRF.

        Returns:
            List of dict hasil gabungan berperingkat tinggi, dilengkapi rrf_score,
            dense_rank, bm25_rank, similarity, dan bm25_score.
        """
        # Dictionary penyimpan data chunk dan kalkulasi skor
        chunk_map: Dict[str, Dict[str, Any]] = {}
        rrf_scores = defaultdict(float)
        dense_ranks = {}
        bm25_ranks = {}

        # 1. Masukkan peringkat Dense Retrieval (1-based rank)
        for rank, res in enumerate(dense_results, start=1):
            cid = res["chunk_id"]
            dense_ranks[cid] = rank
            rrf_scores[cid] += self.weight_dense * (1.0 / (self.rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = {
                    "chunk_id": cid,
                    "text": res["text"],
                    "metadata": res["metadata"],
                    "dense_similarity": res.get("similarity", 0.0),
                    "dense_distance": res.get("distance", 1.0),
                    "bm25_score": 0.0,
                }
            else:
                chunk_map[cid]["dense_similarity"] = res.get("similarity", 0.0)
                chunk_map[cid]["dense_distance"] = res.get("distance", 1.0)

        # 2. Masukkan peringkat BM25 Lexical Retrieval (1-based rank)
        for rank, res in enumerate(bm25_results, start=1):
            cid = res["chunk_id"]
            bm25_ranks[cid] = rank
            rrf_scores[cid] += self.weight_bm25 * (1.0 / (self.rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = {
                    "chunk_id": cid,
                    "text": res["text"],
                    "metadata": res["metadata"],
                    "dense_similarity": 0.0,
                    "dense_distance": 1.0,
                    "bm25_score": res.get("bm25_score", 0.0),
                }
            else:
                chunk_map[cid]["bm25_score"] = res.get("bm25_score", 0.0)

        # 3. Urutkan berdasarkan skor RRF tertinggi
        sorted_cids = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)[:top_k]

        max_possible_rrf = (self.weight_dense / (self.rrf_k + 1)) + (self.weight_bm25 / (self.rrf_k + 1))

        fused_results: List[Dict[str, Any]] = []
        for rank, cid in enumerate(sorted_cids, start=1):
            item = chunk_map[cid]
            raw_rrf = rrf_scores[cid]
            norm_rrf = min(1.0, raw_rrf / max_possible_rrf) if max_possible_rrf > 0 else raw_rrf

            fused_results.append({
                "rank": rank,
                "chunk_id": cid,
                "text": item["text"],
                "metadata": item["metadata"],
                "rrf_score": float(norm_rrf),
                "raw_rrf_score": float(raw_rrf),
                "dense_rank": dense_ranks.get(cid, None),
                "bm25_rank": bm25_ranks.get(cid, None),
                "dense_similarity": item.get("dense_similarity", 0.0),
                "bm25_score": item.get("bm25_score", 0.0),
            })

        return fused_results
