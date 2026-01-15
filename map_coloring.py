from __future__ import annotations
from typing import Dict, Iterable, List, Sequence, Set, Tuple
from ConstraintSatisfactionProblem import ConstraintSatisfactionProblem

# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

"""
Map coloring wrapper for the generic CSP base class.

This module helps you build a map-coloring CSP from human-friendly inputs
(region names, adjacencies, and color names) and pretty-print solutions.

"""

# ******* Encoding *******

class MapEncoding:
    """Holds the name <-> int mappings used to translate solutions."""
    def __init__(self, region_to_int: Dict[str,int], color_to_int: Dict[str,int]):
        self.region_to_int = region_to_int
        self.int_to_region = {i:n for n,i in region_to_int.items()}
        self.color_to_int = color_to_int
        self.int_to_color = {i:c for c,i in color_to_int.items()}
    
# ******* Builder function *******

def build_map_csp(regions: Sequence[str], edges: Iterable[Tuple[str,str]], color_names: Sequence[str]):
    """Build a ConstraintSatisfactionProblem for map coloring.

    Parameters:
        - regions : list of region names (strings)
        - edges : iterable of undirected adjacency pairs (nameA, nameB)
        - color_names : list of color names to use (strings)

    Returns:
        - (csp, encoding) : Tuple[ConstraintSatisfactionProblem, MapEncoding]
    """
    # Map region names and colors to integer ids (0..n-1) and (1..k)
    region_to_int = {name: i for i, name in enumerate(regions)}
    color_to_int = {c: i+1 for i, c in enumerate(color_names)}

    n = len(regions)
    domains = [range(1, len(color_names)+1) for _ in range(n)]
    csp = ConstraintSatisfactionProblem(n, domains)

    # Add not-equal constraints for each undirected edge
    for a, b in edges:
        i, j = region_to_int[a], region_to_int[b]
        if i == j:
            continue
        if i < j:
            csp.add_all_diff_edge(i, j)
        else:
            csp.add_all_diff_edge(j, i)

    enc = MapEncoding(region_to_int, color_to_int)
    return csp, enc

# ******* Nice printing utilities *******

def name_solution(enc: MapEncoding, sol_int: Dict[int,int]) -> Dict[str,str]:
    """Map an integer solution {var:int_color} to {region:color_name}."""
    out: Dict[str,str] = {}
    for var, val in sol_int.items():
        region = enc.int_to_region[var]
        color = enc.int_to_color[val]
        out[region] = color
    return out

def print_named_solution(enc: MapEncoding, sol_int: Dict[int,int]) -> None:
    named = name_solution(enc, sol_int)
    for r in sorted(named):
        print(f"{r:>4s} : {named[r]}")

# ******* Example *******
def australia_example(colors: Sequence[str] = ("red","green","blue")):
    """Return (csp, enc, regions, edges).

    Regions: WA, NT, SA, Q, NSW, V, T (Tasmania (T) has no land borders.)
    """
    regions = ["WA","NT","SA","Q","NSW","V","T"]
    edges = {
        ("WA","NT"), ("WA","SA"), ("NT","SA"), ("NT","Q"), ("SA","Q"),
        ("SA","NSW"), ("SA","V"), ("Q","NSW"), ("NSW","V"),
    }
    csp, enc = build_map_csp(regions, edges, list(colors))
    return csp, enc, regions, edges