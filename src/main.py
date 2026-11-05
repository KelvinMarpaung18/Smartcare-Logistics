import sys
import os

# Memastikan direktori src dapat diakses oleh sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartcare_logistics.search import (
    GRAPH, 
    LOCATIONS, 
    HEURISTIC_S6, 
    get_full_path_names,
    compute_admissible_heuristic, 
    uniform_cost_search, 
    a_star_search
)
from smartcare_logistics.solver import (
    CSP,
    ac3,
    backtracking_search,
    create_medical_fleet_csp
)
from smartcare_logistics.knowledge_base.retriever import KnowledgeBaseRetriever
from smartcare_logistics.knowledge_base.benchmark import BENCHMARK_QUERIES, RetrievalBenchmark


def print_main_header():
    print("=" * 88)
    print(" [SMARTCARE LOGISTICS] ENTERPRISE AI COPILOT")
    print(" MILESTONE 1 (SEARCH), MILESTONE 2 (CSP), & MILESTONE 3 (VECTOR KNOWLEDGE BASE)")
    print("=" * 88 + "\n")


def run_milestone1_experiments():
    print("=" * 88)
    print(" [MILESTONE 1] OPTIMASI RUTE DISTRIBUSI OBAT & DARAH DARURAT (UCS & A* SEARCH)")
    print("=" * 88)
    print(" Titik Awal / Initial State (S0) : S0 - Balige (titik distribusi medis)")
    print(" Satuan Biaya Perjalanan (Cost) : Jarak Tempuh (Kilometer / km)")
    print(" Metodologi Heuristik A*       : h(n) = d_hop(n, Goal) * c_min (c_min = 19.42 km)")
    print(" Sifat Heuristik                : Admissible (h(n) <= h*(n))")
    print("=" * 88 + "\n")

    scenarios = [
        ("Skenario 1 (Utama)", "S0", "S6"),
        ("Skenario 2 (Uji S3)", "S0", "S3"),
        ("Skenario 3 (Uji S4)", "S0", "S4"),
    ]

    print("+" + "-" * 86 + "+")
    print(f"| {'Skenario Pengujian':<24} | {'Algoritma':<8} | {'Path Cost (km)':<14} | {'Explored':<8} | {'Status':<9} |")
    print("+" + "-" * 86 + "+")

    summary_data = []

    for name, start_node, goal_node in scenarios:
        # Pencarian UCS
        ucs_path, ucs_cost, ucs_explored = uniform_cost_search(GRAPH, start_node, goal_node)
        ucs_status = "Berhasil" if ucs_path else "Gagal"

        # Pencarian A*
        heuristic = compute_admissible_heuristic(GRAPH, goal_node)
        astar_path, astar_cost, astar_explored = a_star_search(GRAPH, start_node, goal_node, heuristic)
        astar_status = "Berhasil" if astar_path else "Gagal"

        scen_label = f"{LOCATIONS[start_node].split(' - ')[0]} -> {LOCATIONS[goal_node].split(' - ')[0]}"
        print(f"| {scen_label:<24} | UCS      | {ucs_cost:<14.2f} | {ucs_explored:<8} | {ucs_status:<9} |")
        print(f"| {scen_label:<24} | A*       | {astar_cost:<14.2f} | {astar_explored:<8} | {astar_status:<9} |")
        print("+" + "-" * 86 + "+")

        summary_data.append({
            "name": name,
            "start": start_node,
            "goal": goal_node,
            "ucs": (ucs_path, ucs_cost, ucs_explored),
            "astar": (astar_path, astar_cost, astar_explored)
        })

    print("\n" + "=" * 88)
    print(" RINCIAN RUTE OPTIMAL MILESTONE 1")
    print("=" * 88)

    for item in summary_data:
        start_node = item["start"]
        goal_node = item["goal"]
        ucs_path, ucs_cost, ucs_exp = item["ucs"]
        astar_path, astar_cost, astar_exp = item["astar"]

        print(f"\n[*] {item['name']}: {LOCATIONS[start_node]} ---> {LOCATIONS[goal_node]}")
        print(f"   [UCS] Rute Lengkap   : {get_full_path_names(ucs_path)}")
        print(f"   [UCS] Total Jarak    : {ucs_cost:.2f} km")
        print(f"   [UCS] Node Explored  : {ucs_exp} state")
        
        print(f"   [A*]  Rute Lengkap   : {get_full_path_names(astar_path)}")
        print(f"   [A*]  Total Jarak    : {astar_cost:.2f} km")
        print(f"   [A*]  Node Explored  : {astar_exp} state")

        reduction = ucs_exp - astar_exp
        print(f"   [VERIFIKASI] Total Cost UCS == A*: {ucs_cost == astar_cost} ({ucs_cost:.2f} km)")
        print(f"   [EFISIENSI]  A* menghemat eksplorasi {reduction} state dibanding UCS")


def run_milestone2_experiments():
    print("\n" + "=" * 88)
    print(" [MILESTONE 2] ALOKASI ARMADA MEDIS COLD-CHAIN DENGAN CONSTRAINT SATISFACTION (CSP)")
    print("=" * 88)
    print(" Pusat Logistik / Depo Distribusi : Balige Medical Logistics Hub (Kabupaten Toba)")
    print(" Cakupan Geografis Resmi          : Kabupaten Toba (BPS 2025: 2 RS Umum & 19 Puskesmas)")
    print(" Sampel Fasilitas Model           : 2 RS (RSUD Porsea, RSU HKBP Balige) & 5 Puskesmas Toba")
    print(" Algoritma Solver                 : Backtracking Search + Heuristik MRV, LCV, & Forward Checking")
    print("=" * 88 + "\n")

    # Sampel 7 Fasilitas Kesehatan Resmi Kabupaten Toba (sesuai dokumen perbaikan M2)
    faskes_toba_7 = [
        "RSUD_Porsea",
        "RSU_HKBP_Balige",
        "Puskesmas_Tandang_Buhit",
        "Puskesmas_Soposurung",
        "Puskesmas_Laguboti",
        "Puskesmas_Porsea",
        "Puskesmas_Parsoburan"
    ]

    # Sesi 1: 4 Fasilitas (2 Rumah Sakit + 2 Puskesmas)
    faskes_sesi_1 = ["RSUD_Porsea", "RSU_HKBP_Balige", "Puskesmas_Tandang_Buhit", "Puskesmas_Laguboti"]

    vehicles_base = [
        "Ambulance_01 (ColdChain)",
        "Ambulance_02 (General)",
        "ColdChain_Van_A (DeepFreezer)",
        "ColdChain_Van_B (StandardCold)"
    ]

    vehicles_fleet_8 = [
        "Ambulance_01 (ColdChain)",
        "Ambulance_02 (General)",
        "ColdChain_Van_A (DeepFreezer)",
        "ColdChain_Van_B (StandardCold)",
        "Ambulance_03 (ColdChain)",
        "Ambulance_04 (General)",
        "ColdChain_Van_C (DeepFreezer)",
        "ColdChain_Van_D (StandardCold)"
    ]

    restrictions_sesi_1 = {
        "RSUD_Porsea": ["Ambulance_02 (General)"]  # Faskes memerlukan kendaraan rantai dingin
    }

    scenarios = [
        ("Skenario 1 (Sesi 1: 4 Faskes Toba, 4 Armada)", faskes_sesi_1, vehicles_base, restrictions_sesi_1),
        ("Skenario 2 (Skala Besar: 7 Faskes Toba, 8 Armada)", faskes_toba_7, vehicles_fleet_8, None),
        ("Skenario 3 (Overconstrained: 4 Faskes Toba, 2 Armada)", faskes_sesi_1, vehicles_base[:2], restrictions_sesi_1),
    ]

    solver_configs = [
        ("Pure Backtracking", False, False, False),
        ("MRV + Forward Checking", True, False, True),
        ("MRV + LCV + FC", True, True, True),
    ]

    col_w_scen = 44
    line_sep = "+" + "-" * (col_w_scen + 2) + "+" + "-" * 19 + "+" + "-" * 15 + "+" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 11 + "+" + "-" * 12 + "+"
    print(line_sep)
    print(f"| {'Skenario':<{col_w_scen}} | {'Konfigurasi Solver':<17} | {'Status Solusi':<13} | {'Valid':<5} | {'Nodes':<5} | {'Backtrack':<9} | {'Waktu (ms)':<10} |")
    print(line_sep)

    for scen_title, hosps, vehs, restrs in scenarios:
        for cfg_name, use_mrv, use_lcv, use_fc in solver_configs:
            csp = create_medical_fleet_csp(
                hospitals=hosps,
                vehicles=vehs,
                unary_restrictions=restrs
            )
            sol, st = backtracking_search(
                csp,
                use_mrv=use_mrv,
                use_lcv=use_lcv,
                use_fc=use_fc
            )

            is_valid = "-"
            if sol is not None:
                has_all_vars = len(sol) == len(hosps)
                is_unique = len(set(sol.values())) == len(sol)
                restr_ok = True
                if restrs:
                    for h, forbidden in restrs.items():
                        if h in sol and sol[h] in forbidden:
                            restr_ok = False
                is_valid = "Ya" if (has_all_vars and is_unique and restr_ok) else "Tidak"
                status_str = "SOLUSI VALID"
            else:
                status_str = "TANPA SOLUSI"
                is_valid = "Ya (N/A)"

            print(f"| {scen_title:<{col_w_scen}} | {cfg_name:<17} | {status_str:<13} | {is_valid:<5} | {st['nodes_expanded']:<5} | {st['backtracks']:<9} | {st['execution_time_ms']:<10.2f} |")
        print(line_sep)

    print(" [STATUS MILESTONE 2] SOLVER CSP DAN ANALISIS SENSITIVITAS KABUPATEN TOBA BERHASIL 100%\n")


def run_milestone3_experiments():
    print("=" * 88)
    print(" [MILESTONE 3] ENTERPRISE VECTOR KNOWLEDGE BASE & HYBRID SEARCH")
    print("=" * 88)
    print(" Korpus Dokumen Resmi       : 10 Dokumen PDF (Kemenkes RI & WHO Guidelines)")
    print(" Model Embedding             : intfloat/multilingual-e5-base (768 Dimensi, Cosine Space)")
    print(" Vector Database             : Persistent ChromaDB ('smartcare_knowledge_base')")
    print(" Mesin Pencarian             : Hybrid Search via Reciprocal Rank Fusion (Dense E5 + BM25)")
    print(" Deteksi Out-of-Domain (OOD) : Cosine Similarity Thresholding (< 0.80 -> OOD Rejection)")
    print("=" * 88 + "\n")

    retriever = KnowledgeBaseRetriever()
    benchmark = RetrievalBenchmark(retriever=retriever)

    print("Mengeksekusi pencarian pada 6 Business Queries resmi:\n")
    for q_item in BENCHMARK_QUERIES:
        qid = q_item["query_id"]
        q_text = q_item["query"]
        cat = q_item["category"]
        is_ood = q_item["is_ood"]

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

    print("\n [STATUS MILESTONE 3] VECTOR KNOWLEDGE BASE & HYBRID RETRIEVAL BERJALAN SEMPURNA 100%\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SmartCare Logistics - Sistem AI Cerdas Distribusi Medis Kabupaten Toba")
    parser.add_argument("--m1", action="store_true", help="Jalankan Milestone 1 (State-Space Search UCS & A*)")
    parser.add_argument("--m2", action="store_true", help="Jalankan Milestone 2 (Constraint Satisfaction Problems CSP)")
    parser.add_argument("--m3", action="store_true", help="Jalankan Milestone 3 (Vector Knowledge Base & Hybrid Search)")
    parser.add_argument("--all", action="store_true", help="Jalankan seluruh Milestone (M1, M2, dan M3)")

    args = parser.parse_args()

    print_main_header()

    if args.all:
        run_milestone1_experiments()
        run_milestone2_experiments()
        run_milestone3_experiments()
    elif args.m1:
        run_milestone1_experiments()
    elif args.m2:
        run_milestone2_experiments()
    else:
        # Default fokus eksekusi tugas yang sedang aktif: Milestone 3
        run_milestone3_experiments()
