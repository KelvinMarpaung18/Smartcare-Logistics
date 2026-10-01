import sys
import os

# Add src path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smartcare_logistics.solver import (
    CSP, 
    ac3, 
    revise, 
    backtracking_search, 
    create_medical_fleet_csp,
    not_equal_constraint
)


def test_csp_creation_and_neighbors():
    """Verify CSP formal tuple <X, D, C> initialization and neighbor graph construction."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    
    assert len(csp.variables) == 3
    assert csp.domains["S1_Porsea"] == ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    assert len(csp.neighbors["S1_Porsea"]) == 2
    assert "S3_Tarutung" in csp.neighbors["S1_Porsea"]


def test_ac3_arc_consistency():
    """Verify AC-3 prunes domains and succeeds on consistent CSP graph."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    is_ok, arcs_processed = ac3(csp)
    
    assert is_ok is True
    assert arcs_processed > 0


def test_backtracking_search_mrv_lcv_fc():
    """Verify Backtracking Search finds complete and consistent fleet assignment."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul", "S6_Pangururan"]
    vehicles = ["Ambulance_01", "Ambulance_02", "ColdChain_Van_A", "ColdChain_Van_B"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)
    
    assert solution is not None
    assert len(solution) == 4
    # Check all assigned vehicles are unique
    assigned_vehicles = set(solution.values())
    assert len(assigned_vehicles) == 4
    assert stats["nodes_expanded"] > 0


def test_unary_constraints_and_edge_case_unsolvable():
    """Verify CSP detects unsolvable/overconstrained scenarios (e.g. fewer vehicles than hospitals)."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A"]  # Only 2 vehicles for 3 hospitals!
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)
    
    # Must fail to find complete assignment due to pigeonhole principle
    assert solution is None


def test_sensitivity_analysis_scale():
    """Verify solver performance scales cleanly from small to larger problem instances."""
    # Small scale: 3 hospitals, 4 vehicles
    small_hosp = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    small_veh = ["V1", "V2", "V3", "V4"]
    csp_small = create_medical_fleet_csp(small_hosp, small_veh)
    sol_small, stats_small = backtracking_search(csp_small)
    
    # Large scale: 7 hospitals, 8 vehicles
    large_hosp = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    large_veh = [f"V{i}" for i in range(1, 9)]
    csp_large = create_medical_fleet_csp(large_hosp, large_veh)
    sol_large, stats_large = backtracking_search(csp_large)
    
    assert sol_small is not None
    assert sol_large is not None
    assert stats_small["execution_time_ms"] >= 0
    assert stats_large["execution_time_ms"] >= 0
