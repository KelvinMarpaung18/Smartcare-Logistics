import sys
import os
import pytest

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
    """Memverifikasi algoritma AC-3 berjalan pada graf CSP konsisten."""
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


# ==============================================================================
# PENGUJIAN TAMBAHAN QA & CSP VALIDATION (TUGAS 2)
# ==============================================================================

def test_unary_restriction_valid():
    """Memverifikasi bahwa unary restriction yang valid hanya memangkas armada terlarang pada RS yang bersangkutan."""
    hospitals = ["S1_RSUD_Porsea", "S6_RSUD_Pangururan"]
    vehicles = ["Ambulance_01", "Ambulance_02", "ColdChain_Van_A"]
    unary_restrictions = {
        "S6_RSUD_Pangururan": ["Ambulance_02"]
    }

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)

    # RS S1 harus tetap memiliki semua 3 armada
    assert len(csp.domains["S1_RSUD_Porsea"]) == 3
    assert "Ambulance_02" in csp.domains["S1_RSUD_Porsea"]

    # RS S6 harus terfilter (hanya 2 armada)
    assert len(csp.domains["S6_RSUD_Pangururan"]) == 2
    assert "Ambulance_02" not in csp.domains["S6_RSUD_Pangururan"]
    assert "Ambulance_01" in csp.domains["S6_RSUD_Pangururan"]
    assert "ColdChain_Van_A" in csp.domains["S6_RSUD_Pangururan"]


def test_unary_restriction_empty_domain():
    """Memverifikasi bahwa unary restriction yang membatasi seluruh opsi menghasilkan domain kosong dan dideteksi AC-3."""
    hospitals = ["S1_Porsea"]
    vehicles = ["Ambulance_01", "Ambulance_02"]
    # Batasi semua kendaraan untuk Porsea
    unary_restrictions = {"S1_Porsea": ["Ambulance_01", "Ambulance_02"]}

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)

    assert csp.domains["S1_Porsea"] == []

    # AC-3 harus segera mengenali bahwa CSP tidak konsisten karena domain kosong
    is_ok, arcs_processed = ac3(csp)
    assert is_ok is False
    assert arcs_processed == 0

    # Backtracking search juga harus mengembalikan None dengan 0 ekspansi node
    solution, stats = backtracking_search(csp)
    assert solution is None
    assert stats["nodes_expanded"] == 0


def test_ac3_prunes_inconsistent_domain_values():
    """Memverifikasi bahwa Revise dan AC-3 benar-benar memangkas nilai domain yang kehilangan support konsistensi."""
    # Misal variabel A hanya bisa bernilai V1 (singleton), variabel B bisa V1 atau V2.
    # Dengan constraint A != B, nilai V1 pada B tidak memiliki support pada A, sehingga harus dipangkas.
    variables = ["RS_A", "RS_B"]
    domains = {
        "RS_A": ["V1"],
        "RS_B": ["V1", "V2"]
    }
    csp = CSP(variables, domains)
    csp.add_constraint("RS_A", "RS_B", not_equal_constraint)

    # Sebelum AC-3
    assert len(csp.domains["RS_B"]) == 2
    assert "V1" in csp.domains["RS_B"]

    is_ok, arcs_processed = ac3(csp)

    # Setelah AC-3: V1 pada RS_B harus terhapus karena konflik mutlak dengan RS_A
    assert is_ok is True
    assert arcs_processed > 0
    assert csp.domains["RS_A"] == ["V1"]
    assert csp.domains["RS_B"] == ["V2"]


def test_ac3_domain_wipeout_propagation():
    """Memverifikasi propagasi AC-3 ketika dua variabel saling bertentangan sehingga menyebabkan domain kosong."""
    variables = ["RS_A", "RS_B"]
    domains = {
        "RS_A": ["V1"],
        "RS_B": ["V1"]
    }
    csp = CSP(variables, domains)
    csp.add_constraint("RS_A", "RS_B", not_equal_constraint)

    is_ok, arcs_processed = ac3(csp)

    # Harus mendeteksi domain kosong akibat kendala A != B dengan nilai yang sama
    assert is_ok is False
    assert len(csp.domains["RS_A"]) == 0 or len(csp.domains["RS_B"]) == 0


def test_revise_direct_behavior():
    """Memverifikasi fungsi revise secara langsung untuk kasus prune dan kasus tanpa prune."""
    csp = CSP(["A", "B"], {"A": ["V1", "V2"], "B": ["V1"]})
    csp.add_constraint("A", "B", not_equal_constraint)

    # Merevisi A terhadap B: V1 pada A tidak memiliki pasangan di B karena B hanya punya V1
    # Nilai V1 pada A harus terhapus, menyisakan ['V2']
    revised = revise(csp, "A", "B")
    assert revised is True
    assert csp.domains["A"] == ["V2"]

    # Merevisi kembali A terhadap B: sekarang A=['V2'], B=['V1']. V2 != V1 konsisten.
    revised_again = revise(csp, "A", "B")
    assert revised_again is False

    # Merevisi variabel tanpa relasi constraint
    csp_unrelated = CSP(["X", "Y"], {"X": [1], "Y": [2]})
    assert revise(csp_unrelated, "X", "Y") is False


def test_backtracking_complete_and_valid_solution():
    """Memverifikasi bahwa solusi backtracking selalu lengkap dan memenuhi semua batasan biner dan domain."""
    hospitals = ["RS_1", "RS_2", "RS_3", "RS_4"]
    vehicles = ["V1", "V2", "V3", "V4", "V5"]
    unary_restrictions = {"RS_1": ["V1"]}

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)

    assert solution is not None
    # 1. Kelengkapan: semua variabel memiliki penugasan
    assert len(solution) == len(hospitals)
    for hosp in hospitals:
        assert hosp in solution

    # 2. Validitas domain: nilai terpilih sesuai batasan domain awal
    assert solution["RS_1"] != "V1"
    for hosp in hospitals:
        assert solution[hosp] in vehicles

    # 3. Validitas batasan: All-Different dipenuhi (semua armada unik)
    assigned_values = list(solution.values())
    assert len(assigned_values) == len(set(assigned_values))


def test_invalid_variables_and_domains():
    """Memverifikasi penanganan error saat deklarasi variabel atau domain tidak valid."""
    # 1. Variabel duplikat harus memunculkan ValueError
    with pytest.raises(ValueError, match="duplikasi"):
        CSP(["A", "A"], {"A": [1, 2]})

    # 2. Variabel tanpa definisi domain harus memunculkan ValueError
    with pytest.raises(ValueError, match="Domain tidak ditemukan"):
        CSP(["A", "B"], {"A": [1]})

    # 3. Penambahan batasan pada variabel yang tidak ada harus memunculkan ValueError
    valid_csp = CSP(["A", "B"], {"A": [1], "B": [2]})
    with pytest.raises(ValueError, match="Variabel tidak ditemukan: C"):
        valid_csp.add_constraint("A", "C", not_equal_constraint)


def test_unsolvable_conflicting_unary_restrictions():
    """Memverifikasi kasus tidak ada solusi karena pembatasan unary yang saling mengunci (mutually exclusive)."""
    hospitals = ["RS_Alpha", "RS_Beta"]
    vehicles = ["V1", "V2"]
    # RS_Alpha hanya boleh V1, RS_Beta juga hanya boleh V1
    unary_restrictions = {
        "RS_Alpha": ["V2"],
        "RS_Beta": ["V2"]
    }

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)
    solution, stats = backtracking_search(csp)

    # Karena RS_Alpha dan RS_Beta sama-sama berebut V1 pada graf All-Different, tidak ada solusi
    assert solution is None
    # AC-3 preprocessing mendeteksi inkonsistensi sebelum backtracking berjalan
    assert stats["nodes_expanded"] == 0


def test_search_configurations_comparison():
    """
    Memverifikasi fungsionalitas 4 konfigurasi solver pada skenario terkontrol:
    1. Backtracking Dasar (use_mrv=False, use_lcv=False, use_fc=False)
    2. MRV (use_mrv=True, use_lcv=False, use_fc=False)
    3. MRV + LCV (use_mrv=True, use_lcv=True, use_fc=False)
    4. MRV + LCV + Forward Checking (use_mrv=True, use_lcv=True, use_fc=True)
    """
    hospitals = [
        "S1_RSUD_Porsea",
        "S3_RSUD_Tarutung",
        "S4_RSUD_DolokSanggul",
        "S6_RSUD_Pangururan"
    ]
    vehicles = [
        "Ambulance_01 (ColdChain)",
        "Ambulance_02 (General)",
        "ColdChain_Van_A (DeepFreezer)",
        "ColdChain_Van_B (Standard)"
    ]
    unary_restrictions = {
        "S6_RSUD_Pangururan": ["Ambulance_02 (General)"]
    }

    configs = [
        ("BT_Base", False, False, False),
        ("MRV_Only", True, False, False),
        ("MRV_LCV", True, True, False),
        ("MRV_LCV_FC", True, True, True),
    ]

    for name, use_mrv, use_lcv, use_fc in configs:
        csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)
        solution, stats = backtracking_search(
            csp,
            use_mrv=use_mrv,
            use_lcv=use_lcv,
            use_fc=use_fc
        )

        # Seluruh konfigurasi harus berhasil menemukan solusi valid
        assert solution is not None, f"Gagal pada konfigurasi {name}"
        assert len(solution) == 4
        assert len(set(solution.values())) == 4
        # Batasan unary tetap terpenuhi
        assert solution["S6_RSUD_Pangururan"] != "Ambulance_02 (General)"
        assert stats["nodes_expanded"] > 0

    # Uji verifikasi efisiensi Forward Checking pada kasus overconstrained (4 RS, 2 Armada)
    csp_bt = create_medical_fleet_csp(["A", "B", "C", "D"], ["V1", "V2"])
    sol_bt, stats_bt = backtracking_search(csp_bt, use_mrv=False, use_lcv=False, use_fc=False)

    csp_fc = create_medical_fleet_csp(["A", "B", "C", "D"], ["V1", "V2"])
    sol_fc, stats_fc = backtracking_search(csp_fc, use_mrv=True, use_lcv=True, use_fc=True)

    assert sol_bt is None
    assert sol_fc is None
    # Forward checking memangkas ruang pencarian lebih dini (ekspansi node lebih sedikit)
    assert stats_fc["nodes_expanded"] < stats_bt["nodes_expanded"]


def test_unary_restriction_multiple_and_ignored_keys():
    """Memverifikasi unary restriction untuk banyak RS dan penanganan kunci RS yang tidak terdaftar."""
    hospitals = ["RS_A", "RS_B", "RS_C"]
    vehicles = ["V1", "V2", "V3", "V4"]
    unary_restrictions = {
        "RS_A": ["V1", "V2"],
        "RS_B": ["V3"],
        "RS_UNKNOWN": ["V1"]  # Harus diabaikan secara aman tanpa error
    }

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)

    assert csp.domains["RS_A"] == ["V3", "V4"]
    assert csp.domains["RS_B"] == ["V1", "V2", "V4"]
    assert csp.domains["RS_C"] == ["V1", "V2", "V3", "V4"]


def test_unary_restriction_wipeout_multi_variable():
    """Memverifikasi bahwa domain kosong pada satu variabel di sistem multi-variabel segera membatalkan pencarian."""
    hospitals = ["RS_A", "RS_B", "RS_C"]
    vehicles = ["V1", "V2"]
    # RS_B dilarang menggunakan seluruh kendaraan yang tersedia
    unary_restrictions = {
        "RS_B": ["V1", "V2"]
    }

    csp = create_medical_fleet_csp(hospitals, vehicles, unary_restrictions)
    assert csp.domains["RS_B"] == []

    is_ok, arcs_processed = ac3(csp)
    assert is_ok is False
    assert arcs_processed == 0

    sol, stats = backtracking_search(csp)
    assert sol is None
    assert stats["nodes_expanded"] == 0


def test_ac3_preserves_consistent_domains():
    """Memverifikasi bahwa AC-3 mempertahankan seluruh domain ketika seluruh nilai memiliki support konsisten."""
    hospitals = ["RS_1", "RS_2", "RS_3"]
    vehicles = ["V1", "V2", "V3"]
    csp = create_medical_fleet_csp(hospitals, vehicles)

    original_domains = {h: list(csp.domains[h]) for h in hospitals}
    is_ok, arcs_processed = ac3(csp)

    assert is_ok is True
    assert arcs_processed > 0
    for h in hospitals:
        assert csp.domains[h] == original_domains[h]


def test_ac3_cascade_pruning():
    """
    Memverifikasi propagasi AC-3 bertingkat (cascade):
    A: [V1], B: [V1, V2], C: [V2, V3]
    Constraint: A != B, B != C.
    Revise(B, A) memangkas V1 dari B -> B sisa [V2].
    Revise(C, B) kemudian harus memangkas V2 dari C -> C sisa [V3].
    """
    variables = ["A", "B", "C"]
    domains = {
        "A": ["V1"],
        "B": ["V1", "V2"],
        "C": ["V2", "V3"]
    }
    csp = CSP(variables, domains)
    csp.add_constraint("A", "B", not_equal_constraint)
    csp.add_constraint("B", "C", not_equal_constraint)

    is_ok, arcs_processed = ac3(csp)

    assert is_ok is True
    assert arcs_processed > 0
    assert csp.domains["A"] == ["V1"]
    assert csp.domains["B"] == ["V2"]
    assert csp.domains["C"] == ["V3"]


def test_ac3_chain_wipeout():
    """
    Memverifikasi propagasi AC-3 yang memicu wipeout melalui efek berantai:
    A: [V1], B: [V1, V2], C: [V2]
    Constraint: A != B, B != C.
    Revise(B, A) menghapus V1 dari B -> B: [V2].
    Revise(B, C) menghapus V2 dari B -> B: [] (wipeout).
    """
    variables = ["A", "B", "C"]
    domains = {
        "A": ["V1"],
        "B": ["V1", "V2"],
        "C": ["V2"]
    }
    csp = CSP(variables, domains)
    csp.add_constraint("A", "B", not_equal_constraint)
    csp.add_constraint("B", "C", not_equal_constraint)

    is_ok, arcs_processed = ac3(csp)

    assert is_ok is False
    assert len(csp.domains["B"]) == 0


def test_all_different_large_scale_validity():
    """Memverifikasi validitas alokasi All-Different untuk 7 fasilitas di kawasan Toba."""
    toba_hospitals = [
        "S1_RSUD_Porsea",
        "S2_Siborong_Borong",
        "S3_RSUD_Tarutung",
        "S4_RSUD_Dolok_Sanggul",
        "S5_Tele",
        "S6_RSUD_Pangururan",
        "S7_Parsoburan"
    ]
    vehicles = [f"MedVehicle_{i:02d}" for i in range(1, 9)]  # 8 kendaraan untuk 7 RS

    csp = create_medical_fleet_csp(toba_hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)

    assert solution is not None
    assert len(solution) == 7
    # Seluruh RS mendapatkan kendaraan yang berbeda
    allocated_vehicles = list(solution.values())
    assert len(set(allocated_vehicles)) == 7
    for hosp, veh in solution.items():
        assert veh in vehicles


def test_unsolvable_fewer_vehicles_than_hospitals():
    """Memverifikasi kegagalan solver ketika armada lebih sedikit dari fasilitas (5 RS, 3 Armada)."""
    hospitals = ["RS_1", "RS_2", "RS_3", "RS_4", "RS_5"]
    vehicles = ["V1", "V2", "V3"]

    csp = create_medical_fleet_csp(hospitals, vehicles)
    solution, stats = backtracking_search(csp, use_mrv=True, use_lcv=True, use_fc=True)

    assert solution is None
    assert stats["nodes_expanded"] > 0
    assert stats["backtracks"] > 0


def test_constraint_self_loop_error():
    """Memverifikasi penolakan penambahan binary constraint pada variabel yang sama (self-loop)."""
    csp = CSP(["RS_A"], {"RS_A": ["V1", "V2"]})
    with pytest.raises(ValueError, match="dua variabel yang berbeda"):
        csp.add_constraint("RS_A", "RS_A", not_equal_constraint)


def test_csp_isolated_variables():
    """Memverifikasi penanganan variabel terisolasi (tanpa constraint ke variabel lain)."""
    variables = ["RS_A", "RS_B", "RS_Isolated"]
    domains = {
        "RS_A": ["V1", "V2"],
        "RS_B": ["V1", "V2"],
        "RS_Isolated": ["V3"]
    }
    csp = CSP(variables, domains)
    # Hanya hubungkan RS_A dan RS_B
    csp.add_constraint("RS_A", "RS_B", not_equal_constraint)

    solution, stats = backtracking_search(csp)

    assert solution is not None
    assert len(solution) == 3
    assert solution["RS_Isolated"] == "V3"
    assert solution["RS_A"] != solution["RS_B"]


def test_csp_single_variable():
    """Memverifikasi solver bekerja dengan benar pada CSP dengan satu variabel."""
    csp = CSP(["RS_Single"], {"RS_Single": ["Ambulance_01", "Ambulance_02"]})
    solution, stats = backtracking_search(csp)

    assert solution is not None
    assert len(solution) == 1
    assert solution["RS_Single"] in ["Ambulance_01", "Ambulance_02"]


def test_csp_empty_variables():
    """Memverifikasi penanganan CSP kosong tanpa variabel."""
    csp = CSP([], {})
    solution, stats = backtracking_search(csp)

    assert solution == {}
    assert stats["nodes_expanded"] == 1


def test_mrv_reduces_search_effort_on_heterogeneous_domains():
    """
    Memverifikasi keunggulan heuristik MRV pada masalah dengan ukuran domain heterogen.
    Jika variabel domain besar diletakkan di awal, BT dasar mengeksplorasi cabang salah lebih banyak,
    sedangkan MRV memilih variabel dengan domain paling terbatas terlebih dahulu (fail-first).
    """
    hospitals = ["RS_LargeDomain", "RS_Tight1", "RS_Tight2", "RS_Tight3"]
    vehicles = ["V1", "V2", "V3", "V4"]
    unary = {
        "RS_Tight1": ["V3", "V4"],
        "RS_Tight2": ["V3", "V4"],
        "RS_Tight3": ["V3", "V4"]
    }

    # Tanpa MRV (urutan statis)
    csp_bt = create_medical_fleet_csp(hospitals, vehicles, unary)
    sol_bt, stats_bt = backtracking_search(csp_bt, use_mrv=False, use_lcv=False, use_fc=False)

    # Dengan MRV
    csp_mrv = create_medical_fleet_csp(hospitals, vehicles, unary)
    sol_mrv, stats_mrv = backtracking_search(csp_mrv, use_mrv=True, use_lcv=False, use_fc=False)

    assert sol_bt is None
    assert sol_mrv is None
    # MRV mengeksplorasi jauh lebih sedikit node dibanding urutan statis (5 node vs 15 node)
    assert stats_mrv["nodes_expanded"] < stats_bt["nodes_expanded"]


def test_lcv_avoids_dead_ends():
    """
    Memverifikasi bahwa LCV memilih nilai yang paling sedikit membatasi tetangga,
    sehingga menghindari jalan buntu yang memerlukan backtrack.
    """
    # A: [V1, V3], B: [V1, V2], C: [V1, V2].
    # Semua saling tidak sama (All-Different).
    # Jika A memilih V1 (pilihan default pertama), B dan C berebut V2 -> deadlock -> backtrack.
    # LCV mengenali V3 membatasi 0 nilai tetangga (sedangkan V1 membatasi 2 nilai),
    # sehingga V3 dipilih lebih dahulu dan menghindari backtrack sama sekali.
    csp_no_lcv = CSP(["A", "B", "C"], {
        "A": ["V1", "V3"],
        "B": ["V1", "V2"],
        "C": ["V1", "V2"]
    })
    for v1 in ["A", "B", "C"]:
        for v2 in ["A", "B", "C"]:
            if v1 < v2:
                csp_no_lcv.add_constraint(v1, v2, not_equal_constraint)

    sol_no_lcv, stats_no_lcv = backtracking_search(csp_no_lcv, use_mrv=False, use_lcv=False, use_fc=False)

    csp_lcv = CSP(["A", "B", "C"], {
        "A": ["V1", "V3"],
        "B": ["V1", "V2"],
        "C": ["V1", "V2"]
    })
    for v1 in ["A", "B", "C"]:
        for v2 in ["A", "B", "C"]:
            if v1 < v2:
                csp_lcv.add_constraint(v1, v2, not_equal_constraint)

    sol_lcv, stats_lcv = backtracking_search(csp_lcv, use_mrv=False, use_lcv=True, use_fc=False)

    assert sol_no_lcv == sol_lcv == {"A": "V3", "B": "V1", "C": "V2"}
    assert stats_no_lcv["backtracks"] > 0
    assert stats_lcv["backtracks"] == 0
    assert stats_lcv["nodes_expanded"] < stats_no_lcv["nodes_expanded"]
