from smartcare_logistics.search import (
    GRAPH, 
    LOCATIONS, 
    HEURISTIC_S6, 
    get_full_path_names,
    compute_admissible_heuristic, 
    uniform_cost_search, 
    a_star_search
)

__all__ = [
    "GRAPH", 
    "LOCATIONS", 
    "HEURISTIC_S6", 
    "get_full_path_names",
    "compute_admissible_heuristic", 
    "uniform_cost_search", 
    "a_star_search"
]


def main() -> None:
    from main import run_experiments
    run_experiments()
