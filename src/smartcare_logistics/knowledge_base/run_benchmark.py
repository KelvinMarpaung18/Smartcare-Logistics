"""
Skrip Eksekusi Benchmark Evaluasi Retrieval Milestone 3.
Menjalankan pengujian 6 business queries pada mode Dense, BM25, dan Hybrid RRF.
Menghasilkan metrik Precision@5, Recall@5, MRR, Latency, dan OOD Rejection Rate.
"""

from .benchmark import RetrievalBenchmark
from .retriever import KnowledgeBaseRetriever
from tabulate import tabulate
import json


def main():
    print("=== MEMULAI BENCHMARK EVALUASI RETRIEVAL (Q01 - Q06) ===")
    retriever = KnowledgeBaseRetriever()
    benchmark = RetrievalBenchmark(retriever=retriever)

    results = benchmark.run_benchmark(modes=["dense", "bm25", "hybrid"], top_k=5)

    print("\n--- RINGKASAN PERBANDINGAN PERFORMA RETRIEVAL ---")
    headers = ["Metode Retrieval", "Mean Precision@5", "Mean Recall@5", "Mean MRR", "Avg Latency (ms)", "OOD Rejection (%)"]
    rows = []

    for mode in ["dense", "bm25", "hybrid"]:
        s = results[mode]["summary"]
        rows.append([
            mode.upper(),
            f"{s['mean_precision_at_5']:.4f}",
            f"{s['mean_recall_at_5']:.4f}",
            f"{s['mean_mrr']:.4f}",
            f"{s['average_latency_ms']:.2f} ms",
            f"{s['ood_rejection_rate_percent']:.1f}%",
        ])

    print(tabulate(rows, headers=headers, tablefmt="github"))

    print("\n--- DETAIL HASIL PER QUERY ---")
    for mode in ["dense", "bm25", "hybrid"]:
        print(f"\n[Mode: {mode.upper()}]")
        for q in results[mode]["queries_evaluated"]:
            qid = q["query_id"]
            if q.get("is_ood_expected"):
                print(f"  {qid} (OOD): Rejection Success={q['correct_rejection']} (Sim={q['top_similarity']:.4f}, Latency={q['latency_ms']:.1f}ms)")
            else:
                print(f"  {qid}: P@5={q['precision_at_k']:.2f}, R@5={q['recall_at_k']:.2f}, MRR={q['mrr']:.2f}, Hits={q['relevant_hits']}, TopDocs={q['retrieved_doc_ids'][:3]}")


if __name__ == "__main__":
    main()
