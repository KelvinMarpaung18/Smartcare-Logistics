import sys
import os

# Tambahkan direktori src ke sys.path
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
    """Memverifikasi inisialisasi formal tiga serangkai CSP <X, D, C> dan pembentukan graf tetangga."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    
    assert len(csp.variables) == 3
    assert csp.domains["S1_Porsea"] == ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    assert len(csp.neighbors["S1_Porsea"]) == 2
    assert "S3_Tarutung" in csp.neighbors["S1_Porsea"]


def test_ac3_arc_consistency():
    """Memverifikasi algoritma AC-3 melakukan pemangkasan domain dan berhasil pada graf CSP konsisten."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A", "Drone_Alpha"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    is_ok, arcs_processed = ac3(csp)
    
    assert is_ok is True
    assert arcs_processed > 0


def test_backtracking_search_mrv_lcv_fc():
    """Memverifikasi Backtracking Search berhasil menemukan alokasi armada yang lengkap dan konsisten."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul", "S6_Pangururan"]
    vehicles = ["Ambulance_01", "Ambulance_02", "ColdChain_Van_A", "ColdChain_Van_B"]
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)
    
    assert solution is not None
    assert len(solution) == 4
    # Memastikan seluruh armada yang dialokasikan bersifat unik
    assigned_vehicles = set(solution.values())
    assert len(assigned_vehicles) == 4
    assert stats["nodes_expanded"] > 0


def test_unary_constraints_and_edge_case_unsolvable():
    """Memverifikasi CSP mampu mendeteksi skenario overconstrained/tidak ada solusi (misal armada lebih sedikit dari RS)."""
    hospitals = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    vehicles = ["Ambulance_01", "ColdChain_Van_A"]  # Hanya 2 kendaraan untuk 3 rumah sakit
    
    csp = create_medical_fleet_csp(hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)
    
    # Harus gagal menemukan solusi lengkap sesuai prinsip pigeonhole
    assert solution is None


def test_sensitivity_analysis_scale():
    """Memverifikasi performa solver dapat berskala dari skenario kecil ke skenario besar."""
    # Skala kecil: 3 rumah sakit, 4 armada
    small_hosp = ["S1_Porsea", "S3_Tarutung", "S4_DolokSanggul"]
    small_veh = ["V1", "V2", "V3", "V4"]
    csp_small = create_medical_fleet_csp(small_hosp, small_veh)
    sol_small, stats_small = backtracking_search(csp_small)
    
    # Skala besar: 7 rumah sakit, 8 armada
    large_hosp = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    large_veh = [f"V{i}" for i in range(1, 9)]
    csp_large = create_medical_fleet_csp(large_hosp, large_veh)
    sol_large, stats_large = backtracking_search(csp_large)
    
    assert sol_small is not None
    assert sol_large is not None
    assert stats_small["execution_time_ms"] >= 0
    assert stats_large["execution_time_ms"] >= 0
