import heapq
from collections import deque
from typing import Dict, List, Tuple, Optional

# Definisi Graf Ruang Keadaan untuk Distribusi Pasokan Medis di Wilayah Toba
# Simpul (Nodes): Fasilitas Kesehatan & Pusat Distribusi Medis (S0 hingga S7)
# Busur (Edges): Graf tak berarah (undirected) dengan bobot jarak perjalanan nyata dalam kilometer (km)
GRAPH: Dict[str, Dict[str, float]] = {
    "S0": {"S1": 22.00, "S2": 22.80, "S7": 52.00},
    "S1": {"S0": 22.00},
    "S2": {"S0": 22.80, "S3": 19.42, "S4": 28.53},
    "S3": {"S2": 19.42},
    "S4": {"S2": 28.53, "S5": 40.00},
    "S5": {"S4": 40.00, "S6": 22.00},
    "S6": {"S5": 22.00, "S7": 53.00},
    "S7": {"S0": 52.00, "S6": 53.00}
}

# Pemetaan kode state ke nama fasilitas kesehatan dan lokasi lengkap
LOCATIONS: Dict[str, str] = {
    "S0": "S0 - Balige (titik distribusi medis)",
    "S1": "S1 - RSUD Porsea",
    "S2": "S2 - Siborong-Borong",
    "S3": "S3 - RSUD Tarutung",
    "S4": "S4 - RSUD Dolok Sanggul",
    "S5": "S5 - Tele",
    "S6": "S6 - RSUD dr. Hadrianus Sinaga, Pangururan",
    "S7": "S7 - Parsoburan"
}

# Bobot edge terkecil pada seluruh graf (digunakan untuk formulasi heuristik admissible)
C_MIN: float = 19.42

# Fungsi Heuristik Default h(n) untuk Goal Utama S6 (Pangururan)
# Formula: h(n) = d_hop(n, S6) * C_MIN (di mana C_MIN = 19.42 km)
# Terbukti Admissible: h(n) <= h*(n) untuk seluruh simpul n
HEURISTIC_S6: Dict[str, float] = {
    "S0": 38.84,  # hop minimum = 2 -> 2 * 19.42
    "S1": 58.26,  # hop minimum = 3 -> 3 * 19.42
    "S2": 58.26,  # hop minimum = 3 -> 3 * 19.42
    "S3": 77.68,  # hop minimum = 4 -> 4 * 19.42
    "S4": 38.84,  # hop minimum = 2 -> 2 * 19.42
    "S5": 19.42,  # hop minimum = 1 -> 1 * 19.42
    "S6": 0.00,   # hop minimum = 0 -> 0 * 19.42
    "S7": 19.42   # hop minimum = 1 -> 1 * 19.42
}


def get_full_path_names(path: Optional[List[str]]) -> str:
    """Fungsi pembantu untuk memformat daftar urutan state menjadi string nama fasilitas lengkap."""
    if not path:
        return "Tidak Ada Rute"
    return " -> ".join([LOCATIONS.get(node, node) for node in path])


def compute_admissible_heuristic(
    graph: Dict[str, Dict[str, float]], 
    goal: str, 
    c_min: float = C_MIN
) -> Dict[str, float]:
    """
    Menghitung kamus nilai heuristik admissible untuk sembarang node goal menggunakan jarak hop BFS:
    h(n) = min_hops(n, goal) * c_min.
    Dijamin admissible karena c_min adalah batas bawah biaya edge pada graf.
    """
    heuristic: Dict[str, float] = {}
    if goal not in graph:
        return {node: 0.0 for node in graph}

    # BFS untuk menghitung jumlah hop minimum dari goal ke seluruh node
    queue: deque = deque([(goal, 0)])
    visited_hops: Dict[str, int] = {goal: 0}

    while queue:
        current, hops = queue.popleft()
        for neighbor in graph.get(current, {}):
            if neighbor not in visited_hops:
                visited_hops[neighbor] = hops + 1
                queue.append((neighbor, hops + 1))

    for node in graph:
        hops = visited_hops.get(node, 0)
        heuristic[node] = round(hops * c_min, 2)

    return heuristic


def uniform_cost_search(
    graph: Dict[str, Dict[str, float]], 
    start: str, 
    goal: str
) -> Tuple[Optional[List[str]], float, int]:
    """
    Algoritma Uniform Cost Search (UCS) berbasis priority queue (heapq).
    Mengembalikan tuple (optimal_path, total_cost_km, nodes_explored).
    Uji tujuan (goal test) dilakukan saat node di-pop dari queue.
    """
    if start not in graph or goal not in graph:
        return None, float("inf"), 0

    pq: List[Tuple[float, str, List[str]]] = [(0.0, start, [start])]
    visited: Dict[str, float] = {}
    nodes_explored = 0

    while pq:
        cost, current, path = heapq.heappop(pq)

        if current in visited and visited[current] <= cost:
            continue
        visited[current] = cost
        nodes_explored += 1

        if current == goal:
            return path, cost, nodes_explored

        for neighbor, edge_cost in graph.get(current, {}).items():
            new_cost = cost + edge_cost
            if neighbor not in visited or new_cost < visited[neighbor]:
                heapq.heappush(pq, (new_cost, neighbor, path + [neighbor]))

    return None, float("inf"), nodes_explored


def a_star_search(
    graph: Dict[str, Dict[str, float]], 
    start: str, 
    goal: str, 
    heuristic: Optional[Dict[str, float]] = None
) -> Tuple[Optional[List[str]], float, int]:
    """
    Algoritma A* Search berbasis priority queue (heapq) yang dipandu fungsi heuristik admissible.
    Mengembalikan tuple (optimal_path, total_cost_km, nodes_explored).
    Uji tujuan (goal test) dilakukan saat node di-pop dari queue.
    """
    if start not in graph or goal not in graph:
        return None, float("inf"), 0

    if heuristic is None:
        heuristic = compute_admissible_heuristic(graph, goal)

    initial_h = heuristic.get(start, 0.0)
    # Format Tuple Priority Queue: (f_score, g_score, current, path)
    pq: List[Tuple[float, float, str, List[str]]] = [(initial_h, 0.0, start, [start])]
    visited: Dict[str, float] = {}
    nodes_explored = 0

    while pq:
        f_score, g_score, current, path = heapq.heappop(pq)

        if current in visited and visited[current] <= g_score:
            continue
        visited[current] = g_score
        nodes_explored += 1

        if current == goal:
            return path, g_score, nodes_explored

        for neighbor, edge_cost in graph.get(current, {}).items():
            new_g = g_score + edge_cost
            new_h = heuristic.get(neighbor, 0.0)
            new_f = new_g + new_h

            if neighbor not in visited or new_g < visited[neighbor]:
                heapq.heappush(pq, (new_f, new_g, neighbor, path + [neighbor]))

    return None, float("inf"), nodes_explored
