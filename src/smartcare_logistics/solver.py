"""
SmartCare Logistics - Milestone 2

Modul solver Constraint Satisfaction Problem (CSP) untuk
alokasi armada medis dan kendaraan logistik.

Komponen yang diimplementasikan:
1. CSP: Variables, Domains, dan Constraints
2. AC-3: Arc Consistency 3
3. Backtracking Search
4. MRV: Minimum Remaining Values
5. LCV: Least Constraining Value
6. Forward Checking
"""

import copy
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


Constraint = Callable[[Any, Any], bool]


def not_equal_constraint(value1: Any, value2: Any) -> bool:
    """Memastikan dua variabel tidak menggunakan kendaraan yang sama."""
    return value1 != value2


class CSP:
    """
    Representasi Constraint Satisfaction Problem.

    CSP terdiri dari:
    - variables: himpunan variabel keputusan
    - domains: nilai yang dapat dipilih untuk setiap variabel
    - neighbors: variabel yang memiliki constraint dengan variabel lain
    - constraints: fungsi constraint antar pasangan variabel
    """

    def __init__(
        self,
        variables: List[str],
        domains: Dict[str, List[Any]],
    ) -> None:
        self.variables = list(variables)
        self.domains = {
            variable: list(domain)
            for variable, domain in domains.items()
        }

        self.neighbors: Dict[str, Set[str]] = {
            variable: set()
            for variable in self.variables
        }

        self.constraints: Dict[Tuple[str, str], Constraint] = {}

    def add_constraint(
        self,
        variable1: str,
        variable2: str,
        constraint: Constraint,
    ) -> None:
        """Menambahkan binary constraint antara dua variabel."""

        if variable1 not in self.variables:
            raise ValueError(f"Variabel tidak ditemukan: {variable1}")

        if variable2 not in self.variables:
            raise ValueError(f"Variabel tidak ditemukan: {variable2}")

        self.neighbors[variable1].add(variable2)
        self.neighbors[variable2].add(variable1)

        self.constraints[(variable1, variable2)] = constraint

        # Membuat constraint arah sebaliknya.
        if (variable2, variable1) not in self.constraints:
            self.constraints[(variable2, variable1)] = (
                lambda value2, value1: constraint(value1, value2)
            )

    def is_consistent(
        self,
        variable: str,
        value: Any,
        assignment: Dict[str, Any],
    ) -> bool:
        """
        Memeriksa apakah value dapat diberikan kepada variable
        tanpa melanggar constraint dengan variabel yang sudah
        diberikan nilai.
        """

        for neighbor in self.neighbors[variable]:
            if neighbor not in assignment:
                continue

            neighbor_value = assignment[neighbor]
            constraint = self.constraints.get((variable, neighbor))

            if constraint is not None:
                if not constraint(value, neighbor_value):
                    return False

        return True


def revise(csp: CSP, xi: str, xj: str) -> bool:
    """
    Prosedur Revise pada algoritma AC-3.

    Nilai pada domain Xi dihapus jika tidak memiliki
    nilai pendukung yang valid pada domain Xj.

    Returns:
        True jika domain Xi mengalami perubahan.
        False jika tidak ada perubahan.
    """

    constraint = csp.constraints.get((xi, xj))

    if constraint is None:
        return False

    revised = False
    revised_domain = []

    for value_xi in csp.domains[xi]:
        has_support = any(
            constraint(value_xi, value_xj)
            for value_xj in csp.domains[xj]
        )

        if has_support:
            revised_domain.append(value_xi)
        else:
            revised = True

    if revised:
        csp.domains[xi] = revised_domain

    return revised


def ac3(csp: CSP) -> Tuple[bool, int]:
    """
    Algoritma AC-3 untuk melakukan propagasi constraint.

    Returns:
        Tuple:
        - bool: True jika CSP konsisten, False jika terdapat
          domain kosong.
        - int: jumlah arc yang diproses.
    """

    queue: List[Tuple[str, str]] = [
        (xi, xj)
        for xi in csp.variables
        for xj in csp.neighbors[xi]
    ]

    arcs_processed = 0

    while queue:
        xi, xj = queue.pop(0)
        arcs_processed += 1

        if revise(csp, xi, xj):
            if not csp.domains[xi]:
                return False, arcs_processed

            for xk in csp.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))

    return True, arcs_processed


def select_unassigned_variable_mrv(
    csp: CSP,
    assignment: Dict[str, Any],
) -> str:
    """
    Memilih variabel menggunakan MRV.

    Variabel dengan jumlah nilai domain tersisa paling sedikit
    dipilih terlebih dahulu.

    Jika terjadi tie, digunakan Degree Heuristic:
    variabel dengan tetangga belum terisi paling banyak dipilih.
    """

    unassigned = [
        variable
        for variable in csp.variables
        if variable not in assignment
    ]

    def mrv_key(variable: str) -> Tuple[int, int]:
        domain_size = len(csp.domains[variable])

        unassigned_neighbors = sum(
            1
            for neighbor in csp.neighbors[variable]
            if neighbor not in assignment
        )

        return domain_size, -unassigned_neighbors

    return min(unassigned, key=mrv_key)


def order_domain_values_lcv(
    csp: CSP,
    variable: str,
    assignment: Dict[str, Any],
) -> List[Any]:
    """
    Mengurutkan nilai domain menggunakan LCV.

    Nilai yang paling sedikit membatasi variabel tetangga
    ditempatkan lebih dahulu.
    """

    def count_conflicts(value: Any) -> int:
        conflicts = 0

        for neighbor in csp.neighbors[variable]:
            if neighbor in assignment:
                continue

            constraint = csp.constraints.get((variable, neighbor))

            if constraint is None:
                continue

            for neighbor_value in csp.domains[neighbor]:
                if not constraint(value, neighbor_value):
                    conflicts += 1

        return conflicts

    return sorted(
        csp.domains[variable],
        key=count_conflicts,
    )


def forward_check(
    csp: CSP,
    variable: str,
    value: Any,
    assignment: Dict[str, Any],
) -> Optional[Dict[str, List[Any]]]:
    """
    Forward Checking.

    Setelah variable diberi value, nilai yang tidak konsisten
    di domain tetangganya dihapus.

    Returns:
        Dictionary domain yang sudah dipangkas jika berhasil.
        None jika terdapat domain yang menjadi kosong.
    """

    pruned_domains: Dict[str, List[Any]] = {}

    for neighbor in csp.neighbors[variable]:
        if neighbor in assignment:
            continue

        constraint = csp.constraints.get((variable, neighbor))

        if constraint is None:
            continue

        new_domain = [
            neighbor_value
            for neighbor_value in csp.domains[neighbor]
            if constraint(value, neighbor_value)
        ]

        if not new_domain:
            return None

        pruned_domains[neighbor] = new_domain

    return pruned_domains


def backtracking_search(
    csp: CSP,
    use_mrv: bool = True,
    use_lcv: bool = True,
    use_fc: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Backtracking Search untuk menyelesaikan CSP.

    Secara default menggunakan:
    - AC-3 sebagai preprocessing
    - MRV
    - LCV
    - Forward Checking

    Returns:
        solution:
            Assignment variabel -> nilai, atau None jika tidak ada solusi.

        stats:
            Statistik proses pencarian.
    """

    stats: Dict[str, Any] = {
        "nodes_expanded": 0,
        "backtracks": 0,
        "ac3_arcs_processed": 0,
        "execution_time_ms": 0.0,
    }

    start_time = time.perf_counter()

    # Salinan agar CSP asli tidak berubah.
    local_csp = copy.deepcopy(csp)

    # Preprocessing menggunakan AC-3.
    ac3_ok, arcs_processed = ac3(local_csp)

    stats["ac3_arcs_processed"] = arcs_processed

    if not ac3_ok:
        stats["execution_time_ms"] = (
            time.perf_counter() - start_time
        ) * 1000.0

        return None, stats

    def backtrack(
        assignment: Dict[str, Any],
        current_csp: CSP,
    ) -> Optional[Dict[str, Any]]:

        stats["nodes_expanded"] += 1

        # Semua variabel sudah memiliki nilai.
        if len(assignment) == len(current_csp.variables):
            return assignment.copy()

        # Pemilihan variabel.
        if use_mrv:
            variable = select_unassigned_variable_mrv(
                current_csp,
                assignment,
            )
        else:
            variable = next(
                variable
                for variable in current_csp.variables
                if variable not in assignment
            )

        # Pengurutan domain.
        if use_lcv:
            values = order_domain_values_lcv(
                current_csp,
                variable,
                assignment,
            )
        else:
            values = list(current_csp.domains[variable])

        for value in values:

            if not current_csp.is_consistent(
                variable,
                value,
                assignment,
            ):
                continue

            assignment[variable] = value

            # Simpan domain sebelum dilakukan pruning.
            saved_domains = {
                var: list(current_csp.domains[var])
                for var in current_csp.variables
            }

            branch_success = True

            if use_fc:
                pruned_domains = forward_check(
                    current_csp,
                    variable,
                    value,
                    assignment,
                )

                if pruned_domains is None:
                    branch_success = False
                else:
                    for neighbor, domain in pruned_domains.items():
                        current_csp.domains[neighbor] = domain

            if branch_success:
                result = backtrack(
                    assignment,
                    current_csp,
                )

                if result is not None:
                    return result

            # Kembalikan domain sebelum mencoba cabang berikutnya.
            current_csp.domains = saved_domains

            del assignment[variable]

            stats["backtracks"] += 1

        return None

    solution = backtrack({}, local_csp)

    stats["execution_time_ms"] = (
        time.perf_counter() - start_time
    ) * 1000.0

    return solution, stats


def create_medical_fleet_csp(
    hospitals: List[str],
    vehicles: List[str],
    unary_restrictions: Optional[Dict[str, List[str]]] = None,
) -> CSP:
    """
    Membuat CSP untuk alokasi armada medis.

    Variables:
        Fasilitas kesehatan tujuan.

    Domains:
        Kendaraan yang tersedia.

    Constraints:
        1. Unary restriction untuk kebutuhan kendaraan tertentu.
        2. Binary constraint All-Different agar satu kendaraan
           tidak digunakan oleh dua fasilitas pada sesi yang sama.
    """

    domains = {
        hospital: list(vehicles)
        for hospital in hospitals
    }

    # Unary restrictions.
    if unary_restrictions:
        for hospital, restricted_vehicles in unary_restrictions.items():
            if hospital in domains:
                domains[hospital] = [
                    vehicle
                    for vehicle in domains[hospital]
                    if vehicle not in restricted_vehicles
                ]

    csp = CSP(
        variables=hospitals,
        domains=domains,
    )

    # Binary All-Different constraint.
    for index, hospital1 in enumerate(hospitals):
        for hospital2 in hospitals[index + 1:]:
            csp.add_constraint(
                hospital1,
                hospital2,
                not_equal_constraint,
            )

    return csp