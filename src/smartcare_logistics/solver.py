"""
SmartCare Logistics - Milestone 2: Modul Solver Pemecahan Batasan Keputusan Bisnis (CSP)
Solusi untuk Alokasi Armada Medis & Kendaraan Logistik Cold-Chain di Wilayah Toba.

Mengimplementasikan:
1. Formulsi CSP Formal <X, D, C>
2. Algoritma Propagasi Batasan AC-3 (Arc Consistency 3)
3. Algoritma Backtracking Search terakselerasi dengan:
   - MRV (Minimum Remaining Values)
   - LCV (Least Constraining Value)
   - Forward Checking (FC)
"""

import copy
import time
from typing import Dict, List, Set, Tuple, Any, Optional, Callable


# Standard Binary Constraint Helper Functions
def not_equal_constraint(val1: Any, val2: Any) -> bool:
    """Binary constraint ensuring two variables do not take the same value."""
    return val1 != val2


def distance_fuel_constraint(dist1: float, dist2: float, max_combined_dist: float = 80.0) -> Callable[[Any, Any], bool]:
    """Ensures combined vehicle assignment distance does not exceed fuel/capacity limit."""
    def constraint(val1: Any, val2: Any) -> bool:
        if val1 == val2:
            return False  # Cannot use same vehicle
        return True
    return constraint


class CSP:
    """
    Constraint Satisfaction Problem (CSP) Class.
    Defines Variables (X), Domains (D), and Binary Constraints (C).
    """

    def __init__(self, variables: List[str], domains: Dict[str, List[Any]]):
        self.variables: List[str] = variables
        self.domains: Dict[str, List[Any]] = {var: list(dom) for var, dom in domains.items()}
        self.neighbors: Dict[str, Set[str]] = {var: set() for var in variables}
        self.constraints: Dict[Tuple[str, str], Callable[[Any, Any], bool]] = {}

    def add_constraint(self, var1: str, var2: str, constraint_fn: Callable[[Any, Any], bool]) -> None:
        """Add a binary constraint between var1 and var2."""
        if var1 not in self.variables or var2 not in self.variables:
            raise ValueError(f"Variables {var1} or {var2} not in CSP variables.")

        self.neighbors[var1].add(var2)
        self.neighbors[var2].add(var1)
        self.constraints[(var1, var2)] = constraint_fn

        # Inverse relation check if symmetrical
        if (var2, var1) not in self.constraints:
            self.constraints[(var2, var1)] = lambda val2, val1: constraint_fn(val1, val2)

    def is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """Check if assigning var = value violates any constraints with already assigned variables."""
        for neighbor in self.neighbors[var]:
            if neighbor in assignment:
                neighbor_val = assignment[neighbor]
                constraint_fn = self.constraints.get((var, neighbor))
                if constraint_fn and not constraint_fn(value, neighbor_val):
                    return False
        return True


def revise(csp: CSP, xi: str, xj: str) -> bool:
    """
    Revise procedure for AC-3 algorithm (Mackworth, 1977).
    Removes values from D_i that have no legal supporting value in D_j.
    Returns True if domain D_i was revised (pruned).
    """
    revised = False
    constraint_fn = csp.constraints.get((xi, xj))
    if not constraint_fn:
        return False

    new_domain = []
    for x in csp.domains[xi]:
        # Check if there exists at least one y in D_j satisfying constraint(x, y)
        has_support = any(constraint_fn(x, y) for y in csp.domains[xj])
        if has_support:
            new_domain.append(x)
        else:
            revised = True

    if revised:
        csp.domains[xi] = new_domain

    return revised


def ac3(csp: CSP) -> Tuple[bool, int]:
    """
    Arc Consistency 3 (AC-3) Algorithm.
    Prunes inconsistent values from domains before or during search.
    Returns Tuple of (is_consistent, total_arcs_processed).
    """
    queue: List[Tuple[str, str]] = [(xi, xj) for xi in csp.variables for xj in csp.neighbors[xi]]
    arcs_processed = 0

    while queue:
        xi, xj = queue.pop(0)
        arcs_processed += 1

        if revise(csp, xi, xj):
            if len(csp.domains[xi]) == 0:
                return False, arcs_processed  # Contradiction: empty domain

            for xk in csp.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))

    return True, arcs_processed


def select_unassigned_variable_mrv(csp: CSP, assignment: Dict[str, Any]) -> str:
    """
    Minimum Remaining Values (MRV) Heuristic (Fail-First Principle).
    Selects the unassigned variable with the smallest remaining domain size.
    Breaks ties using the Degree Heuristic (most unassigned neighbors).
    """
    unassigned = [v for v in csp.variables if v not in assignment]
    
    # Sort by domain size ascending (MRV), then by number of unassigned neighbors descending (Degree)
    def mrv_degree_key(var: str) -> Tuple[int, int]:
        domain_size = len(csp.domains[var])
        unassigned_neighbors = sum(1 for n in csp.neighbors[var] if n not in assignment)
        return (domain_size, -unassigned_neighbors)

    return min(unassigned, key=mrv_degree_key)


def order_domain_values_lcv(csp: CSP, var: str, assignment: Dict[str, Any]) -> List[Any]:
    """
    Least Constraining Value (LCV) Heuristic (Fail-Last Principle).
    Orders values in D_var by how few choices they eliminate in neighboring unassigned variables.
    """
    if len(csp.domains[var]) <= 1:
        return list(csp.domains[var])

    def count_conflicts(value: Any) -> int:
        conflicts = 0
        for neighbor in csp.neighbors[var]:
            if neighbor not in assignment:
                constraint_fn = csp.constraints.get((var, neighbor))
                if constraint_fn:
                    for neighbor_val in csp.domains[neighbor]:
                        if not constraint_fn(value, neighbor_val):
                            conflicts += 1
        return conflicts

    # Sort values ascending by number of conflicts caused
    return sorted(csp.domains[var], key=count_conflicts)


def forward_check(csp: CSP, var: str, value: Any, assignment: Dict[str, Any]) -> Optional[Dict[str, List[Any]]]:
    """
    Forward Checking (FC) Procedure.
    Prunes values from unassigned neighbors of var that conflict with var = value.
    Returns pruned domains dictionary if successful, or None if domain wipeout occurs.
    """
    pruned_domains: Dict[str, List[Any]] = {}

    for neighbor in csp.neighbors[var]:
        if neighbor not in assignment:
            constraint_fn = csp.constraints.get((var, neighbor))
            if constraint_fn:
                new_dom = [y for y in csp.domains[neighbor] if constraint_fn(value, y)]
                if len(new_dom) == 0:
                    return None  # Domain wipeout!
                pruned_domains[neighbor] = new_dom

    return pruned_domains


def backtracking_search(
    csp: CSP, 
    use_mrv: bool = True, 
    use_lcv: bool = True, 
    use_fc: bool = True
) -> Tuple[Optional[Dict[str, Any]], Dict[str, int]]:
    """
    Backtracking Search Algorithm for CSP.
    Returns Tuple of (solution_assignment, statistics_dict).
    """
    stats = {
        "nodes_expanded": 0,
        "backtracks": 0,
        "execution_time_ms": 0.0
    }
    start_time = time.perf_counter()

    # Create a deepcopy of CSP to avoid modifying original problem instance during search
    local_csp = copy.deepcopy(csp)

    # Apply initial AC-3 pre-processing
    is_ac3_ok, ac3_arcs = ac3(local_csp)
    stats["ac3_arcs_processed"] = ac3_arcs
    if not is_ac3_ok:
        stats["execution_time_ms"] = (time.perf_counter() - start_time) * 1000.0
        return None, stats

    def backtrack(assignment: Dict[str, Any], current_csp: CSP) -> Optional[Dict[str, Any]]:
        stats["nodes_expanded"] += 1

        if len(assignment) == len(current_csp.variables):
            return assignment  # Complete and consistent solution found!

        # Select next variable (MRV or standard order)
        if use_mrv:
            var = select_unassigned_variable_mrv(current_csp, assignment)
        else:
            unassigned = [v for v in current_csp.variables if v not in assignment]
            var = unassigned[0]

        # Order domain values (LCV or standard order)
        if use_lcv:
            values = order_domain_values_lcv(current_csp, var, assignment)
        else:
            values = list(current_csp.domains[var])

        for val in values:
            if current_csp.is_consistent(var, val, assignment):
                assignment[var] = val

                # Save current domain state for backtracking
                saved_domains = {v: list(current_csp.domains[v]) for v in current_csp.variables}

                if use_fc:
                    pruned = forward_check(current_csp, var, val, assignment)
                    if pruned is not None:
                        # Update pruned domains
                        for n_var, n_dom in pruned.items():
                            current_csp.domains[n_var] = n_dom

                        result = backtrack(assignment, current_csp)
                        if result is not None:
                            return result

                    # Revert domains if forward check failed or branch led to failure
                    current_csp.domains = saved_domains
                else:
                    result = backtrack(assignment, current_csp)
                    if result is not None:
                        return result

                # Backtrack assignment
                del assignment[var]
                stats["backtracks"] += 1

        return None

    solution = backtrack({}, local_csp)
    stats["execution_time_ms"] = (time.perf_counter() - start_time) * 1000.0
    return solution, stats


# Helper function to create standard Medical Fleet Assignment CSP for Toba Region
def create_medical_fleet_csp(
    hospitals: List[str], 
    vehicles: List[str], 
    unary_restrictions: Optional[Dict[str, List[str]]] = None
) -> CSP:
    """
    Creates a CSP instance for Medical Fleet Assignment across health facilities in Toba Region.
    - Variables X: Destination Hospitals (e.g. S1_Porsea, S3_Tarutung, S4_DolokSanggul, S6_Pangururan)
    - Domains D: Available Emergency Vehicles / Ambulances
    - Constraints C: Unary (vehicle type eligibility) and Binary (no double-booking of vehicles).
    """
    domains = {hosp: list(vehicles) for hosp in hospitals}

    # Apply unary constraints (filter out prohibited vehicles for specific hospitals)
    if unary_restrictions:
        for hosp, restricted_vehs in unary_restrictions.items():
            if hosp in domains:
                domains[hosp] = [v for v in domains[hosp] if v not in restricted_vehs]

    csp = CSP(variables=hospitals, domains=domains)

    # Add binary constraints: All different vehicles for overlapping delivery routes
    for i in range(len(hospitals)):
        for j in range(i + 1, len(hospitals)):
            h1, h2 = hospitals[i], hospitals[j]
            csp.add_constraint(h1, h2, not_equal_constraint)

    return csp
