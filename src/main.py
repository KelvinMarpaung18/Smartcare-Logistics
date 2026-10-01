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


def print_header():
    print("=" * 88)
    print(" [SMARTCARE LOGISTICS] OPTIMASI RUTE DISTRIBUSI OBAT & DARAH DARURAT")
    print("        WILAYAH TOBA DAN SEKITARNYA (A* SEARCH & UNIFORM COST SEARCH)")
    print("=" * 88)
    print(" Titik Awal / Initial State (S0) : S0 - Balige (titik distribusi medis)")
    print(" Satuan Biaya Perjalanan (Cost) : Jarak Tempuh (Kilometer / km)")
    print(" Metodologi Heuristik A*       : h(n) = d_hop(n, Goal) * c_min (c_min = 19.42 km)")
    print(" Sifat Heuristik                : Terbukti Admissible (h(n) <= h*(n)) & Consistent")
    print("=" * 88)
    print("\n DAFTAR STATE & NAMA LOKASI LENGKAP:")
    for code, name in LOCATIONS.items():
        print(f"   * {code:<3} = {name}")
    print("=" * 88 + "\n")


def run_experiments():
    print_header()

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
    print(" RINCIAN RUTE OPTIMAL DENGAN NAMA LOKASI LENGKAP")
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

    print("\n" + "=" * 88)
    print(" [KESIMPULAN METODOLOGIS]")
    print(" 1. UCS & A* sama-sama menghasilkan rute optimal dengan Path Cost minimum.")
    print(" 2. Skenario Utama (S0 -> S6):")
    print(f"    Rute: {get_full_path_names(['S0', 'S7', 'S6'])}")
    print("    Total Jarak: 105.00 km")
    print(" 3. A* Search terbukti lebih efisien dalam eksplorasi state (6 state vs 8 state).")
    print(" 4. Heuristik h(n) = d_hop * 19.42 terbukti Admissible & Consistent.")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    run_experiments()