from __future__ import annotations
from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

"""
Backtracking CSP solver with optional heuristics and inference

This module implements a generic backtracking search that operates on the
ConstraintSatisfactionProblem interface defined in our base class. 
It supports the heuristics: MRV (minimum remaing values), degree heuristic, and LCV (least constraining value).
It support AC-3 (arc consistency) inference.

Usage
-----
result = backtracking_search(csp, variable_strategy="mrv+degree", use_lcv=True, inference="ac3")
Other examples:
    - No heuristics: backtracking_search(csp, variable_strategy="none", use_lcv=False, inference="none")
    - Degree only: backtracking_search(csp, variable_strategy="degree", use_lcv=False, inference="none")
    - MRV only: backtracking_search(csp, variable_strategy="mrv", use_lcv=False, inference="none")
Returns a dict {var: value} on success, or None on failure.
"""

# ********* Inference: AC-3 *********
def ac3(csp) -> bool:
    """Run AC-3 to enforce arc consistency on the given CSP instance.

    Returns True if arc consistency is achieved; False if any domain becomes empty.
    """
    Q = deque(csp.arcs())
    while Q:
        (xi, xj) = Q.popleft()
        if csp.revise(xi, xj):
            if not csp.domain(xi):
                return False
            for xk in csp.neighbors_of(xi):
                if xk != xj:
                    Q.append((xk, xi))
    return True

# ********* Heuristics *********
def select_unassigned_variable(csp, assignment: Dict[int, int], variable_strategy: str) -> int:
    """Choose the next variable to assign.

    variable_strategy options:
        - "none": pick the first unassigned variable (no heuristic)
        - "mrv": minimum remaining values only
        - "degree": degree heuristic only (most constraints on unassigned neighbors)
        - "mrv+degree": MRV with degree tiebreak among ties (default)
    """
    unassigned = [v for v in range(csp.n_vars) if v not in assignment]
    if not unassigned:
        raise ValueError("select_unassigned_variable called with complete assignment")

    if variable_strategy == "none":
        return unassigned[0]

    if variable_strategy == "degree":
        def deg(v: int) -> int:
            return sum(1 for nb in csp.neighbors_of(v) if nb not in assignment)
        return max(unassigned, key=deg)

    if variable_strategy == "mrv":
        return min(unassigned, key=lambda v: len(csp.domain(v)))

    if variable_strategy == "mrv+degree":
        # MRV first
        min_size = min(len(csp.domain(v)) for v in unassigned)
        candidates = [v for v in unassigned if len(csp.domain(v)) == min_size]
        if len(candidates) == 1:
            return candidates[0]
        # Degree tiebreak among the MRV ties
        def deg(v: int) -> int:
            return sum(1 for nb in csp.neighbors_of(v) if nb not in assignment)
        return max(candidates, key=deg)
    
    raise ValueError("variable_strategy must be one of {'none','mrv','degree','mrv+degree'}")

def order_domain_values(csp, var: int, assignment: Dict[int, int], use_lcv: bool) -> List[int]:
    """Return values for `var` in the order to try.

    LCV score: for value `val`, count how many values it rules out across
    all unassigned neighbors of `var`. Lower score first.
    """
    values = list(csp.domain(var)) # snapshot list
    if not use_lcv:
        return values
    
    def lcv_score(val: int) -> int:
        score = 0
        for nb in csp.neighbors_of(var):
            if nb in assignment:
                continue
            # Count neighbor values that would be disallowed if var=val
            for nb_val in csp.domain(nb):
                if not csp.is_pair_allowed(var, val, nb, nb_val):
                    score += 1
        return score

    return sorted(values, key=lcv_score)

# ********* Consistency *********

def is_locally_consistent(csp, var: int, val: int, assignment: Dict[int, int]) -> bool:
    """Check (var=val) against already-assigned neighbors only."""
    for nb, nb_val in assignment.items():
        # Only need to check if there's a constraint between var and nb; the
        # CSP method will treat missing constraints as vacuously satisfied.
        if not csp.is_pair_allowed(var, val, nb, nb_val):
            return False
        if not csp.is_pair_allowed(nb, nb_val, var, val):
            # If constraints are stored directionally, also check the reverse
            return False
    return True

# ********* Backtracking *********

# variable_strategy can be: 'none', 'mrv', 'degree', or 'mrv+degree'
# inference is "none" or "ac3"
def backtracking_search(csp, *, variable_strategy: str = "mrv+degree", use_lcv: bool = True, inference: str = "ac3"):
    """Solve the CSP using backtracking with optional heuristics/inference.
    Returns a dict {var: value} if a solution is found, else None.
    """

    def recurse(csp_node, assignment: Dict[int, int]):
        # Goal test: all variables assigned
        if len(assignment) == csp_node.n_vars:
            return assignment

        var = select_unassigned_variable(csp_node, assignment, variable_strategy)
        for val in order_domain_values(csp_node, var, assignment, use_lcv):
            if not is_locally_consistent(csp_node, var, val, assignment):
                continue

            # Create child node with var fixed to val
            child = csp_node.copy_with_domains()
            child.domain(var).clear()
            child.domain(var).add(val)

            # Inference
            if inference == "ac3":
                if not ac3(child):
                    continue
            elif inference == "none":
                pass
            else:
                raise ValueError("inference must be 'none' or 'ac3'")

            # Early failure if any domain wiped out by inference
            if any(len(child.domain(v)) == 0 for v in range(child.n_vars)):
                continue

            assignment[var] = val
            result = recurse(child, assignment)
            if result is not None:
                return result
            # backtrack
            assignment.pop(var)

        return None
    return recurse(csp, {})


if __name__ == "__main__":
    print("This module provides backtracking_search(csp, ...) — import and call it from your tests.")