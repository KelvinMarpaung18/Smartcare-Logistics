import sys
import os

# Ensure src path is available
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


def print_main_header():
    print("=" * 88)
    print(" [SMARTCARE LOGISTICS] ENTERPRISE AI COPILOT")
    print(" MILESTONE 1 (SEARCH) & MILESTONE 2 (CONSTRAINT SATISFACTION PROBLEMS / CSP)")
    print("=" * 88 + "\n")


def run_milestone1_experiments():
    print("=" * 88)
    print(" [MILESTONE 1] OPTIMASI RUTE DISTRIBUSI OBAT & DARAH DARURAT (UCS & A* SEARCH)")
    print("=" * 88)
    print(" Titik Awal / Initial State (S0) : S0 - Balige (titik distribusi medis)")
    print(" Satuan Biaya Perjalanan (Cost) : Jarak Tempuh (Kilometer / km)")
    print(" Metodologi Heuristik A*       : h(n) = d_hop(n, Goal) * c_min (c_min = 19.42 km)")
    print(" Sifat Heuristik                :  Admissible (h(n) <= h*(n))")
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
        # UCS Search
        ucs_path, ucs_cost, ucs_explored = uniform_cost_search(GRAPH, start_node, goal_node)
        ucs_status = "Berhasil" if ucs_path else "Gagal"

        # A* Search
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
    print(" [MILESTONE 2] MODUL PEMECAHAN BATASAN KEPUTUSAN BISNIS (CSP / CONSTRAINT SATISFACTION)")
    print(" ALOKASI ARMADA KENDARAAN MEDIS & AMBULANS LOGISTIK COLD-CHAIN DI WILAYAH TOBA")
    print("=" * 88)
    print(" Formulasi Tiga Serangkai CSP  : < X (Variabel), D (Domain), C (Batasan Binari/Unary) >")
    print(" Algoritma Inferensi           : Arc Consistency 3 (AC-3) & Backtracking Search")
    print(" Heuristik Akselerasi          : Minimum Remaining Values (MRV) + Least Constraining Value (LCV)")
    print(" Propagasi Selama Pencarian    : Forward Checking (FC)")
    print("=" * 88 + "\n")

    # Defined Case Study: Emergency Ambulance & Medical Supply Fleet Allocation
    hospitals = [
        "S1_RSUD_Porsea", 
        "S3_RSUD_Tarutung", 
        "S4_RSUD_DolokSanggul", 
        "S6_RSUD_Pangururan"
    ]
    
    fleet_vehicles = [
        "Ambulance_01 (ColdChain)", 
        "Ambulance_02 (General)", 
        "ColdChain_Van_A (DeepFreezer)", 
        "ColdChain_Van_B (Standard)"
    ]

    unary_restrictions = {
        "S6_RSUD_Pangururan": ["Ambulance_02 (General)"]  # Pangururan requires Deep Freezing or ColdChain Van
    }

    print("[1/3] Membangun Model CSP Formal Alokasi Armada Medis...")
    csp = create_medical_fleet_csp(hospitals, fleet_vehicles, unary_restrictions)
    
    print(f"      -> Total Variabel X (Fasilitas) : {len(csp.variables)}")
    print(f"      -> Total Domain D (Armada)     : {len(fleet_vehicles)} opsi kendaraan")
    print(f"      -> Total Arc Batasan C (Biner)  : {len(csp.constraints)} pasangan arc\n")

    print("[2/3] Menguji Propagasi Batasan AC-3 (Arc Consistency 3)...")
    is_ac3_ok, arcs_processed = ac3(csp)
    print(f"      -> AC-3 Status                 : {'LULUS (Graf Konsisten)' if is_ac3_ok else 'GAGAL (Domain Kosong)'}")
    print(f"      -> Arc Diproses   : {arcs_processed} arc\n")

    print("[3/3] Menjalankan Backtracking Search (MRV + LCV + Forward Checking)...")
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)

    if solution:
        print("      -> SOLUSI LEGAL & KONSISTEN DITEMUKAN:")
        for hosp, veh in solution.items():
            print(f"         * {hosp:<22} <== Assigned to ==> {veh}")
        print(f"      -> Stat Pencarian             : Node Ekspansi={stats['nodes_expanded']}, Backtracks={stats['backtracks']}, Waktu={stats['execution_time_ms']:.2f} ms\n")
    else:
        print("      -> Solusi tidak ditemukan!\n")

    print("-" * 88)
    print(" ANALYSIS SENSITIVITAS SKALA PERMASALAHAN (SMALL VS LARGE VS OVERCONSTRAINED EDGE CASE)")
    print("-" * 88)

    test_cases = [
        ("Skala Kecil (3 RS, 4 Armada)", ["S1", "S3", "S4"], ["V1", "V2", "V3", "V4"], None),
        ("Skala Besar (7 RS, 8 Armada)", ["S1", "S2", "S3", "S4", "S5", "S6", "S7"], [f"V{i}" for i in range(1, 9)], None),
        ("Kasus Ekstrem (Overconstrained: 4 RS, 2 Armada)", ["S1", "S2", "S3", "S4"], ["V1", "V2"], None)
    ]

    print(f"| {'Kasus Uji Sensitivitas':<46} | {'Status Solusi':<15} | {'Node':<6} | {'Waktu (ms)':<10} |")
    print("+" + "-" * 86 + "+")

    for title, hosps, vehs, restrs in test_cases:
        test_csp = create_medical_fleet_csp(hosps, vehs, restrs)
        sol, st = backtracking_search(test_csp)
        status_str = "SOLUSI VALID" if sol else "TIDAK ADA SOLUSI"
        print(f"| {title:<46} | {status_str:<15} | {st['nodes_expanded']:<6} | {st['execution_time_ms']:<10.2f} |")

    print("+" + "-" * 86 + "+")
    print(" [STATUS MILESTONE 2] SOLVER CSP DAN ANALISIS SENSITIVITAS BERHASIL TEREKSEKUSI 100%\n")


if __name__ == "__main__":
    print_main_header()
    run_milestone1_experiments()
    run_milestone2_experiments()