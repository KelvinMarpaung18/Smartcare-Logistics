"""
Modul Benchmark & Evaluasi Kualitas Retrieval Knowledge Base.
Mengevaluasi kinerja Dense Retrieval, BM25 Lexical, dan Hybrid RRF
berdasarkan 6 Business Queries resmi (termasuk Out-of-Domain query).
"""

from typing import List, Dict, Any, Optional
import time
import json
from pathlib import Path

from .config import BENCHMARK_DIR
from .retriever import KnowledgeBaseRetriever


BENCHMARK_QUERIES: List[Dict[str, Any]] = [
    {
        "query_id": "Q01",
        "category": "Vaccine Cold Chain & Puskesmas",
        "query": "Berapa standar suhu penyimpanan cold chain vaksin sensitif beku di Puskesmas dan cold box?",
        "expected_docs": ["DOC01", "DOC06", "DOC09"],
        "expected_keywords": ["2°C", "8°C", "vaksin", "suhu", "cold", "chain", "beku", "penyimpanan"],
        "is_ood": False,
    },
    {
        "query_id": "Q02",
        "category": "Hospital Pharmacy Management",
        "query": "Bagaimana prosedur penerimaan, verifikasi faktur, dan penyimpanan sediaan farmasi di Rumah Sakit?",
        "expected_docs": ["DOC03", "DOC08"],
        "expected_keywords": ["penerimaan", "penyimpanan", "farmasi", "rumah sakit", "faktur", "verifikasi"],
        "is_ood": False,
    },
    {
        "query_id": "Q03",
        "category": "Regulatory Amendment (DOC02 & DOC01)",
        "query": "Apa saja perubahan regulasi standar pelayanan kefarmasian di Puskesmas menurut Permenkes 26 Tahun 2020?",
        "expected_docs": ["DOC02", "DOC01"],
        "expected_keywords": ["Permenkes", "26", "2020", "perubahan", "pelayanan kefarmasian", "Puskesmas"],
        "is_ood": False,
    },
    {
        "query_id": "Q04",
        "category": "WHO & National Vaccine Shipping Guidelines",
        "query": "Bagaimana pedoman pengkondisian cool packs dan pengemasan vaksin saat distribusi?",
        "expected_docs": ["DOC06", "DOC08", "DOC09", "DOC10"],
        "expected_keywords": ["cool packs", "ice packs", "packaging", "vaccines", "shipping", "WHO"],
        "is_ood": False,
    },
    {
        "query_id": "Q05",
        "category": "Policy & Strategic Planning (DOC07)",
        "query": "Apa arah kebijakan dan target rencana aksi Direktorat Imunisasi untuk pengelolaan logistik imunisasi tahun 2025-2029?",
        "expected_docs": ["DOC07"],
        "expected_keywords": ["rencana aksi", "2025-2029", "Direktorat Imunisasi", "kebijakan", "target"],
        "is_ood": False,
    },
    {
        "query_id": "Q06",
        "category": "Out-of-Domain (OOD Rejection Test)",
        "query": "Bagaimana resep bumbu memasak ikan mas arsik khas Balige Danau Toba?",
        "expected_docs": [],
        "expected_keywords": ["ikan mas", "arsik", "andaliman", "resep"],
        "is_ood": True,
    },
]


class RetrievalBenchmark:
    """
    Evaluator benchmark retrieval untuk mengukur Precision@K, Recall@K, MRR, dan OOD rejection.
    """

    def __init__(self, retriever: Optional[KnowledgeBaseRetriever] = None):
        self.retriever = retriever or KnowledgeBaseRetriever()

    def evaluate_query(
        self,
        query_item: Dict[str, Any],
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Mengevaluasi satu query dan menghitung metrik relevansinya.
        """
        qid = query_item["query_id"]
        q_text = query_item["query"]
        expected_docs = set(query_item["expected_docs"])
        is_ood_query = query_item["is_ood"]

        res = self.retriever.search(q_text, mode=mode, top_k=top_k)
        retrieved_items = res["results"]
        is_system_ood = res["is_out_of_domain"]

        if is_ood_query:
            # Query OOD dinilai berdasarkan keberhasilan menolak (True Rejection)
            correct_rejection = is_system_ood
            return {
                "query_id": qid,
                "mode": mode,
                "is_ood_expected": True,
                "is_ood_predicted": is_system_ood,
                "correct_rejection": correct_rejection,
                "precision_at_k": 1.0 if correct_rejection else 0.0,
                "recall_at_k": 1.0 if correct_rejection else 0.0,
                "mrr": 1.0 if correct_rejection else 0.0,
                "top_similarity": res.get("top_similarity", 0.0),
                "latency_ms": res.get("latency_ms", 0.0),
                "retrieved_doc_ids": [it.get("metadata", {}).get("document_id") for it in retrieved_items],
            }

        # Query In-Domain: hitung Precision@K, Recall@K, dan Reciprocal Rank (RR)
        retrieved_docs = []
        relevant_hits = 0
        rr = 0.0

        for rank, it in enumerate(retrieved_items, start=1):
            doc_id = it.get("metadata", {}).get("document_id")
            retrieved_docs.append(doc_id)
            if doc_id in expected_docs:
                relevant_hits += 1
                if rr == 0.0:
                    rr = 1.0 / rank

        p_at_k = relevant_hits / top_k if top_k > 0 else 0.0
        r_at_k = len(set(retrieved_docs).intersection(expected_docs)) / len(expected_docs) if expected_docs else 0.0

        return {
            "query_id": qid,
            "mode": mode,
            "is_ood_expected": False,
            "is_ood_predicted": is_system_ood,
            "relevant_hits": relevant_hits,
            "precision_at_k": round(p_at_k, 4),
            "recall_at_k": round(r_at_k, 4),
            "mrr": round(rr, 4),
            "top_similarity": res.get("top_similarity", 0.0),
            "latency_ms": res.get("latency_ms", 0.0),
            "retrieved_doc_ids": retrieved_docs,
        }

    def run_benchmark(self, modes: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Menjalankan benchmark lengkap untuk mode 'dense', 'bm25', dan 'hybrid'.
        """
        if modes is None:
            modes = ["dense", "bm25", "hybrid"]

        BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
        benchmark_results = {}

        for mode in modes:
            mode_evals = []
            in_domain_p = []
            in_domain_r = []
            in_domain_mrr = []
            latencies = []
            ood_success = 0
            ood_total = 0

            for q in BENCHMARK_QUERIES:
                eval_res = self.evaluate_query(q, mode=mode, top_k=top_k)
                mode_evals.append(eval_res)
                latencies.append(eval_res["latency_ms"])

                if q["is_ood"]:
                    ood_total += 1
                    if eval_res.get("correct_rejection"):
                        ood_success += 1
                else:
                    in_domain_p.append(eval_res["precision_at_k"])
                    in_domain_r.append(eval_res["recall_at_k"])
                    in_domain_mrr.append(eval_res["mrr"])

            avg_p = sum(in_domain_p) / len(in_domain_p) if in_domain_p else 0.0
            avg_r = sum(in_domain_r) / len(in_domain_r) if in_domain_r else 0.0
            avg_mrr = sum(in_domain_mrr) / len(in_domain_mrr) if in_domain_mrr else 0.0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
            ood_rate = (ood_success / ood_total) * 100.0 if ood_total > 0 else 0.0

            benchmark_results[mode] = {
                "queries_evaluated": mode_evals,
                "summary": {
                    "mean_precision_at_5": round(avg_p, 4),
                    "mean_recall_at_5": round(avg_r, 4),
                    "mean_mrr": round(avg_mrr, 4),
                    "average_latency_ms": round(avg_lat, 2),
                    "ood_rejection_rate_percent": round(ood_rate, 2),
                },
            }

        # Simpan hasil benchmark ke JSON
        output_file = BENCHMARK_DIR / "retrieval_benchmark_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_results, f, ensure_ascii=False, indent=2)

        return benchmark_results
