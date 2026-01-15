from __future__ import annotations
from typing import Dict, Iterable, List, Sequence, Tuple, Optional
from ConstraintSatisfactionProblem import ConstraintSatisfactionProblem

# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

"""
Circuit-board layout as a CSP

Variables: one per component. The value for variable i is the (x,y) lower-left
position of that component on the board, encoded as an integer id.
Domains: all positions (x,y) such that the rectangle fits: 0 <= x <= W-w_i and
0 <= y <= H-h_i.
Constraints: pairwise non-overlap between every pair of components.
Two axis-aligned rectangles A and B do not overlap iff at least one of:
    - xA + wA <= xB or xB + wB <= xA or
    - yA + hA <= yB or yB + hB <= yA

We build the generic `ConstraintSatisfactionProblem` with integer domains and
explicit compatibility tables (directed arcs) computed from the geometry above.

Pretty-printing: `render_ascii(...)` draws the board with characters for each
component (first letter of its name by default).
"""
# ******* Data classes *******
class Part:
    def __init__(self, name: str, w: int, h: int, char: Optional[str] = None):
        self.name = name
        self.w = int(w)
        self.h = int(h)
        self.char = (char if char is not None else (name[0] if name else "#"))

class BoardEncoding:
    """Holds per-variable (x,y) <-> int value maps for pretty-printing."""
    def __init__(self, id_to_pos: List[Dict[int, Tuple[int,int]]]):
        self.id_to_pos = id_to_pos # list indexed by var; each is {val_id:(x,y)}

# ******* Utilities *******

def fits(board_w: int, board_h: int, x: int, y: int, w: int, h: int) -> bool:
    return 0 <= x and 0 <= y and x + w <= board_w and y + h <= board_h

def rects_overlap(p1: Tuple[int,int], w1: int, h1: int, p2: Tuple[int,int], w2: int, h2: int) -> bool:
    x1, y1 = p1; x2, y2 = p2
    # NOT (separated horizontally or vertically)
    sep = (x1 + w1 <= x2) or (x2 + w2 <= x1) or (y1 + h1 <= y2) or (y2 + h2 <= y1)
    return not sep

# ******* CSP Builder *******

def build_board_csp(board_w: int, board_h: int, parts: Sequence[Part]):
    """Create (csp, encoding) for the board layout problem.

    Each variable i corresponds to parts[i]. The domain of i is all placement
    ids (integers) for valid lower-left positions within the board.
    """
    n = len(parts)

    # Build per-variable encodings - enumerate all legal placements.
    id_to_pos: List[Dict[int, Tuple[int,int]]] = []
    domains: List[Iterable[int]] = []
    for i, p in enumerate(parts):
        mapping: Dict[int, Tuple[int,int]] = {}
        next_id = 0
        for x in range(0, board_w - p.w + 1):
            for y in range(0, board_h - p.h + 1):
                if fits(board_w, board_h, x, y, p.w, p.h):
                    mapping[next_id] = (x, y)
                    next_id += 1
        id_to_pos.append(mapping)
        domains.append(mapping.keys()) # iterable of int ids

    csp = ConstraintSatisfactionProblem(n, domains)

    # Add non-overlap constraints for each pair of parts (both directions)
    for i in range(n):
        for j in range(i + 1, n):
            rel_ij = set()
            for vi, pi in id_to_pos[i].items():
                for vj, pj in id_to_pos[j].items():
                    if not rects_overlap(pi, parts[i].w, parts[i].h, pj, parts[j].w, parts[j].h):
                        rel_ij.add((vi, vj))
            # Install symmetric relation (j,i) by swapping pairs
            csp.add_binary_constraint(i, j, rel_ij)
            csp.add_binary_constraint(j, i, {(vj, vi) for (vi, vj) in rel_ij})

    enc = BoardEncoding(id_to_pos)
    return csp, enc

# ******* Pretty-printers *******

def decode_solution_positions(enc: BoardEncoding, sol: Dict[int,int]) -> Dict[int, Tuple[int,int]]:
    return {i: enc.id_to_pos[i][v] for i, v in sol.items()}

def render_ascii(board_w: int, board_h: int, parts: Sequence[Part], sol: Dict[int,int], enc: BoardEncoding) -> str:
    grid = [["." for _ in range(board_w)] for _ in range(board_h)]
    pos = decode_solution_positions(enc, sol)
    for i, (x, y) in pos.items():
        p = parts[i]
        for dx in range(p.w):
            for dy in range(p.h):
                gx, gy = x + dx, y + dy
                # y is from bottom; render with row 0 as top, so flip vertically
                grid[board_h - 1 - gy][gx] = p.char
    return "\n".join("".join(row) for row in grid)

# ******* Example case *******
def example_from_prompt():
    """Return (W,H,parts) describing the 10x3 example used in the handout.

    Parts and sizes:
    - e: 7x1
    - a: 3x2
    - b: 5x2
    - c: 2x3
    """
    W, H = 10, 3
    parts = [
        Part("a", 3, 2, "a"),
        Part("b", 5, 2, "b"),
        Part("c", 2, 3, "c"),
        Part("e", 7, 1, "e"),
    ]
    return W, H, parts