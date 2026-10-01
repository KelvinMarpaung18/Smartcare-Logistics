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
    revise,
    backtracking_search,
    select_unassigned_variable_mrv,
    order_domain_values_lcv,
    forward_check,
    create_medical_fleet_csp,
    not_equal_constraint
)

__all__ = [
    # Milestone 1: State-Space Search
    "GRAPH", 
    "LOCATIONS", 
    "HEURISTIC_S6", 
    "get_full_path_names",
    "compute_admissible_heuristic", 
    "uniform_cost_search", 
    "a_star_search",
    # Milestone 2: CSP Solver
    "CSP",
    "ac3",
    "revise",
    "backtracking_search",
    "select_unassigned_variable_mrv",
    "order_domain_values_lcv",
    "forward_check",
    "create_medical_fleet_csp",
    "not_equal_constraint"
]


def main() -> None:
    from main import run_experiments
    run_experiments()
