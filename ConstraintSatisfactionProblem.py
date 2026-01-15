from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

"""
Constraint Satisfaction Problem (CSP) base class

This module defines a generic CSP with integer variable indices and integer
domain values, as recommended in the assisgnment instructions' Design notes.
The Goal is to keep the solver and problem-specific code separate from this
core representation.

Key ideas:
    - Variables are 0..(n-1).
    - Domains are a list of sets of integers:
        - `domains[i]` is the current domain for variable i.
    - Constraints are binary and stored as a diredcted compatability table:
        - `allowed[(i, j)]` is the set of value pairs (vi, vj) that satisfy the constraint
           for variable i versus variable j in that order. This directed form is convenient for AC-3
           because arcs are directional.
    - Neighbors are derived from the constraint table cached in `neighbors[i] = {}` for quick look ups in inference/heuristics.
    
"""

Value = int
Var = int
Pair = Tuple[Value, Value]
Arc = Tuple[Var, Var] # Directional

@dataclass(frozen=True)
class Assignment:
    """
    Lightweight assignment wrapper used by solvers.

    `values[i]` is either an int (a chosen value) or `None` if unassigned.
    The class is immutable so backtracking is safer; solvers may build a new
    Assignment with an update instead of mutating current one in place.
    """
    values: Tuple[Optional[Value], ...]

    def is_complete(self) -> bool:
        return all(v is not None for v in self.values)

    def value_of(self, var: Var) -> Optional[Value]:
        return self.values[var]

    def with_pair(self, var: Var, val: Value) -> Assignment:
        lst = list(self.values)
        lst[var] = val
        return Assignment(tuple(lst))

class ConstraintSatisfactionProblem:
    """
    Generic CSP with integer variables and binary constraints.

    Parameters:
        - n_vars : int
            Number of variables (indices 0..n_vars-1)
        - domains : Sequence[Iterable[int]]  *Set is not a Sequence
            Initial domain for each variable. Each element is converted
            into a set so membership/removal is constant time (O(1)). Domains must be non-empty.

    Represenation Invariants:
        - `len(self.domains) == n_vars` and each domain is non-empty.
        - `self.allowed[(i, j)]` (if present) is a set of allowed (vi, vj) pairs.
          Absence of a key means no constraint between i and j.
        - `self.neighbors[i]` contains exactly those `j` for which either
          `(i, j)` or `(j, i)` is present in `self.allowed`.
    """ 

    def __init__(self, n_vars: int, domains: Sequence[Iterable[int]]):
        assert n_vars > 0, "CSP must have at least one variable"
        assert len(domains) == n_vars, "One domain per variable is required"
        self.n_vars: int = n_vars
        self.domains: List[Set[Value]] = [set(d) for d in domains]
        for i, d in enumerate(self.domains):
            if not d:
                raise ValueError(f"Domain for variable {i} is empty at init")

        # Directed compatibility table for binary constraints
        self.allowed: Dict[Arc, Set[Pair]] = {}
        # Neighbor cache for quick graph access (used by heuristics and inference)
        self.neighbors: List[Set[Var]] = [set() for _ in range(n_vars)]


    # ***************** Constraint construction helpers *****************

    def add_binary_constraint(self, i: Var, j: Var, allowed_pairs: Iterable[Pair]) -> None:
        """Add/replace the directed constraint table for arc (i, j).

        `allowed_pairs` must contain only values in current domains.
        This does **not** automatically add the reverse (j, i); call this twice
        for asymmetric relations, or use `add_symmetric_binary_constraint` function.
        """
        if i == j:
            raise ValueError("Self-constraints should be expressed by modifying (shrinking) variable's domain directly.")
        table: Set[Pair] = set()
        Di, Dj = self.domains[i], self.domains[j]
        for (vi, vj) in allowed_pairs:
            if vi in Di and vj in Dj:
                table.add((vi, vj))
            else:
                pass # Out-of-domain pairs are ignored - they could never be chosen.
        self.allowed[(i, j)] = table

        # Update neighbor structure
        self.neighbors[i].add(j)
        self.neighbors[j].add(i)

    def add_symmetric_binary_constraint(self, i: Var, j: Var, relation: Iterable[Pair]) -> None:
        """Convenience: add the same compatibility in both directions.

        For each (vi, vj) in relation, we also allow (vj, vi) for (j, i).
        Use this function for common symmetric relations like "not equal".
        """
        rel = set(relation)
        self.add_binary_constraint(i, j, rel)
        self.add_binary_constraint(j, i, {(vj, vi) for (vi, vj) in rel})

    def add_all_diff_edge(self, i: Var, j: Var) -> None:
        """Add a standard "i != j" constraint in both directions.

        Legal pairs are all (vi, vj) with vi != vj, respecting the current domains.
        """
        Di, Dj = self.domains[i], self.domains[j]
        rel_ij = {(vi, vj) for vi in Di for vj in Dj if vi != vj}
        rel_ji = {(vj, vi) for (vi, vj) in rel_ij}
        self.allowed[(i, j)] = rel_ij
        self.allowed[(j, i)] = rel_ji
        self.neighbors[i].add(j)
        self.neighbors[j].add(i)


    # ***************** Read-only helpers used by solvers/heuristics *****************

    def domain(self, var: Var) -> Set[Value]:
        """Return the actual domain set for `var` (mutable, shared with the CSP state).

        If you will remove values during iteration (e.g., in AC-3/forward-checking),
        iterate over a snapshot (e.g. tuple(csp.domain(var))) to avoid mutating a set you are looping on:
        """
        return self.domains[var]

    def copy_with_domains(self) -> ConstraintSatisfactionProblem:
        """Return a CSP whose domains, constraint tables, and neighbor sets are new copies.

        Use this to create independent search nodes: pruning in the clone won't affect
        the original (and vice versa)."""

        clone = ConstraintSatisfactionProblem(self.n_vars, [set(d) for d in self.domains]) # Deep copy of each domain set

        clone.allowed = {k: set(v) for k, v in self.allowed.items()} # Actualy copy the constraint tables too for safety - no accidental mutation.
        clone.neighbors = [set(N) for N in self.neighbors]
        return clone

    def neighbors_of(self, var: Var) -> Set[Var]:
        return self.neighbors[var]

    def arcs(self) -> Iterable[Arc]:
        """Yield all directional arcs (Xi, Xj) that currently have constraints."""
        return self.allowed.keys()
    

    # ***************** Consistency checks used by backtracking and LCV *****************
    def is_pair_allowed(self, i: Var, vi: Value, j: Var, vj: Value) -> bool:
        """Return True iff assignment (i=vi, j=vj) satisfies the constraint.
        If there is no constraint between i and j, the pair is vacuously allowed.
        """
        table = self.allowed.get((i, j))
        return True if table is None else (vi, vj) in table

    def is_value_consistent_with(self, var: Var, val: Value, partial: Assignment) -> bool:
        """Check local consistency of assigning `var = val` against `partial`.

        This implements the textbook predicate used inside backtracking: a
        value is consistent if it does not violate any constraint with already
        assigned neighbors.

        Essentially, the goal is to test whether assigning `var = val` would violate any constraints with already-assigned neighbors
        in a partial assignment.
        """
        for j in self.neighbors_of(var):
            vj = partial.value_of(j) # read neighbor j's curent value in the partial assignment
            if vj is None: # None means "unassigned yet"
                continue # skip thsi neighbor - no violation possible
            if not self.is_pair_allowed(var, val, j, vj):
                return False # conflict with assigned neighbor -> inconsistent
        return True # no conflicts with any assigned neighbor
    
    # ***************** Domain pruning helpers (used by AC-3 and forward checking) *****************
    def remove_from_domain(self, var: Var, val: Value) -> bool:
        """Remove `val` from `var`'s domain. Return True iff a removal occurred."""
        if val in self.domains[var]:
            self.domains[var].remove(val)
            return True
        return False

    def revise(self, xi: Var, xj: Var) -> bool:
        """For, AC-3: remove values from Di that have no supporting value in Dj.

        Returns True iff any value was removed from Di.
        If there is no constraint from (xi, xj), this function does nothing.
        """
        table = self.allowed.get((xi, xj))
        if table is None:
            return False
        removed = False
        Di, Dj = self.domain(xi), self.domain(xj)
        # For each vi in Di, check if there exists vj in Dj such that (vi, vj) is allowed
        for vi in tuple(Di): # iterate over snapshot because we may remove
            supported = any((vi, vj) in table for vj in Dj)
            if not supported:
                Di.remove(vi)
                removed = True
        return removed