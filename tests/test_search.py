import sys
import os

# Add src path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smartcare_logistics.search import (
    GRAPH, 
    HEURISTIC_S6, 
    compute_admissible_heuristic, 
    uniform_cost_search, 
    a_star_search
)


def test_main_scenario_s0_to_s6():
    """Verify S0 -> S6 main scenario results match report (105.00 km, UCS=8 state, A*=6 state)."""
    ucs_path, ucs_cost, ucs_explored = uniform_cost_search(GRAPH, "S0", "S6")
    astar_path, astar_cost, astar_explored = a_star_search(GRAPH, "S0", "S6", HEURISTIC_S6)

    assert ucs_path == ["S0", "S7", "S6"]
    assert round(ucs_cost, 2) == 105.00
    assert ucs_explored == 8

    assert astar_path == ["S0", "S7", "S6"]
    assert round(astar_cost, 2) == 105.00
    assert astar_explored == 6

    # Verify A* explores fewer nodes than UCS
    assert astar_explored < ucs_explored


def test_scenario_s0_to_s3():
    """Verify S0 -> S3 scenario results match report (42.22 km, UCS=4 state, A*=3 state)."""
    ucs_path, ucs_cost, ucs_explored = uniform_cost_search(GRAPH, "S0", "S3")
    heuristic_s3 = compute_admissible_heuristic(GRAPH, "S3")
    astar_path, astar_cost, astar_explored = a_star_search(GRAPH, "S0", "S3", heuristic_s3)

    assert ucs_path == ["S0", "S2", "S3"]
    assert round(ucs_cost, 2) == 42.22
    assert ucs_explored == 4

    assert astar_path == ["S0", "S2", "S3"]
    assert round(astar_cost, 2) == 42.22
    assert astar_explored == 3


def test_scenario_s0_to_s4():
    """Verify S0 -> S4 scenario results match report (51.33 km, UCS=5 state, A*=3 state)."""
    ucs_path, ucs_cost, ucs_explored = uniform_cost_search(GRAPH, "S0", "S4")
    heuristic_s4 = compute_admissible_heuristic(GRAPH, "S4")
    astar_path, astar_cost, astar_explored = a_star_search(GRAPH, "S0", "S4", heuristic_s4)

    assert ucs_path == ["S0", "S2", "S4"]
    assert round(ucs_cost, 2) == 51.33
    assert ucs_explored == 5

    assert astar_path == ["S0", "S2", "S4"]
    assert round(astar_cost, 2) == 51.33
    assert astar_explored == 3


def test_heuristic_admissibility_proof():
    """Verify that heuristic h(n) <= h*(n) (true minimum cost to goal S6) for all nodes."""
    goal = "S6"
    for node in GRAPH:
        _, true_cost, _ = uniform_cost_search(GRAPH, node, goal)
        h_val = HEURISTIC_S6[node]
        assert h_val <= true_cost, f"Heuristic overestimates at node {node}: {h_val} > {true_cost}"


def test_dynamic_heuristic_generator():
    """Verify dynamic compute_admissible_heuristic produces valid admissible values."""
    heuristic_s6_calc = compute_admissible_heuristic(GRAPH, "S6")
    for node in GRAPH:
        assert heuristic_s6_calc[node] == HEURISTIC_S6[node]


def test_edge_case_unreachable_node():
    """Verify search handles disconnected nodes gracefully."""
    disconnected_graph = {
        "Node_A": {"Node_B": 10.0},
        "Node_B": {"Node_A": 10.0},
        "Isolated_Node": {}
    }
    path, cost, explored = uniform_cost_search(disconnected_graph, "Node_A", "Isolated_Node")
    assert path is None
    assert cost == float("inf")


def test_edge_case_start_equals_goal():
    """Verify search returns 0 cost when start node equals goal node."""
    path, cost, explored = uniform_cost_search(GRAPH, "S0", "S0")
    assert path == ["S0"]
    assert cost == 0.0
    assert explored == 1