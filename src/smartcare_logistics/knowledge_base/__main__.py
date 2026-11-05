"""
Entrypoint eksekusi langsung paket Knowledge Base Milestone 3.
Menjalankan pencarian semantik hibrida dan evaluasi benchmark query resmi.
"""

from .benchmark import BENCHMARK_QUERIES
from .retriever import KnowledgeBaseRetriever
from tabulate import tabulate


def main():
    print("=" * 88)
    print(" [SMARTCARE LOGISTICS] MILESTONE 3: VECTOR KNOWLEDGE BASE & HYBRID SEARCH")
    print("=" * 88)
    print(" Korpus Dokumen Resmi       : 10 Dokumen PDF (Kemenkes RI & WHO Guidelines)")
    print(" Model Embedding             : intfloat/multilingual-e5-base (768 Dimensi, Cosine Space)")
    print(" Vector Database             : Persistent ChromaDB ('smartcare_knowledge_base')")
    print(" Mesin Pencarian             : Hybrid Search via Reciprocal Rank Fusion (Dense E5 + BM25)")
    print(" Deteksi Out-of-Domain (OOD) : Cosine Similarity Thresholding (< 0.80 -> OOD Rejection)")
    print("=" * 88 + "\n")

    retriever = KnowledgeBaseRetriever()

    print("Mengeksekusi pencarian pada 6 Business Queries resmi:\n")
    for q_item in BENCHMARK_QUERIES:
        qid = q_item["query_id"]
        q_text = q_item["query"]
        cat = q_item["category"]

        res = retriever.search(q_text, mode="hybrid", top_k=3)
        status_ood = "DITOLAK SEBAGAI OUT-OF-DOMAIN" if res["is_out_of_domain"] else "VALID (IN-DOMAIN)"

        print(f"[*] {qid} [{cat}]")
        print(f"   Query               : \"{q_text}\"")
        print(f"   Status Klasifikasi  : {status_ood} (Top Similarity: {res['top_similarity']:.4f})")
        print(f"   Response Latency    : {res['latency_ms']:.2f} ms")

        if res["is_out_of_domain"]:
            print(f"   Pesan Sistem        : {res['warning']}")
        else:
            print("   Top Dokumen Terkait :")
            for r in res["results"][:2]:
                doc_name = r["metadata"].get("file_name", "Unknown")
                page_start = r["metadata"].get("page_start", "?")
                rrf_sc = r.get("rrf_score", 0.0)
                snippet = r["text"][:120].replace("\n", " ") + "..."
                print(f"     - [{r['chunk_id']}] {doc_name} (Hal {page_start}) | RRF Score: {rrf_sc:.4f}")
                print(f"       Kutipan: \"{snippet}\"")
        print("-" * 88)

    print("\n [STATUS MILESTONE 3] KNOWLEDGE BASE & HYBRID SEARCH SELESAI TEREKSEKUSI 100%\n")


if __name__ == "__main__":
    main()
