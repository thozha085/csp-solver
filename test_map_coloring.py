from __future__ import annotations
import time
from typing import Dict
from ConstraintSatisfactionProblem import ConstraintSatisfactionProblem
from solver import backtracking_search
from map_coloring import australia_example, name_solution

# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

"""
Test driver for the map-coloring CSP. Runs with and without heuristics and
with and without AC-3.

Run:
    python3 test_map_coloring.py
"""

def run_combo(csp, enc, *, variable_strategy: str, use_lcv: bool, inference: str) -> Dict[int,int] | None:
    t0 = time.perf_counter()
    sol = backtracking_search(csp.copy_with_domains(), variable_strategy=variable_strategy, use_lcv=use_lcv, inference=inference)
    dt = (time.perf_counter() - t0) * 1000
    named = name_solution(enc, sol) if sol else None
    print(f"strategy={variable_strategy:11s} LCV={str(use_lcv):5s} inference={inference:4s} time={dt:7.2f} ms -> {named}")
    return sol

def main():
    print("*** Australia map-coloring (3 colors) ***")
    csp, enc, regions, edges = australia_example()

    # With and without heuristics and inference
    for vs in ["none", "degree", "mrv", "mrv+degree"]:
        for inf in ["none", "ac3"]:
            for lcv in [False, True]:
                run_combo(csp, enc, variable_strategy=vs, use_lcv=lcv, inference=inf)

    # Quick unsatisfiable test check: try to color Australia with 2 colors
    print("\n*** Australia with only 2 colors (expect None) ***")
    csp2, enc2, _, _ = australia_example(colors=("red","green"))
    run_combo(csp2, enc2, variable_strategy="mrv+degree", use_lcv=True, inference="ac3")

if __name__ == "__main__":
    main()