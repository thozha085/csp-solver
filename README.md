## Summary

This project builds a generic CSP solver (backtracking + optional MRV/degree/LCV + optional AC-3) and
uses it by translating two problems into the same CSP format: **variables, domains, and binary constraints**.

---

## Generic CSP Solver

### Core CSP representation
- **Variables:** indexed `0..n-1`
- **Domains:** each variable has a set of **integer values**
- **Binary constraints:** stored as **directed compatibility tables** (allowed-pair relations)
  - For each directed arc `(Xi, Xj)`, we store the set of allowed pairs `(vi, vj)`
  - This directed form is convenient for arc-based inference (AC-3)

### How it solves
- **Backtracking search** assigns variables one-by-one and checks consistency against constraints
- Optional heuristics to improve performance:
  - **MRV (Minimum Remaining Values):** choose the unassigned variable with the smallest remaining domain
  - **Degree heuristic (tie-break):** prefer the variable that constrains the most unassigned neighbors
  - **LCV (Least Constraining Value):** try values that eliminate the fewest choices for neighboring variables
- Optional inference:
  - **AC-3 (Arc Consistency):** prunes domain values that have no supporting value in a neighbor’s domain

---

## CSP Formulation: Map Coloring

- **Variables:** one variable per region (e.g., WA, NT, SA, ...)
- **Domains:** the set of available colors (encoded as integers)
- **Constraints:** for every adjacent pair of regions `(Ri, Rj)`, enforce **different colors**:
  - `Ri != Rj`
  - Implemented as a binary allowed-pair relation on the arcs between neighboring regions

---

## CSP Formulation: Circuit-Board Layout (2D Rectangle Packing)

- **Variables:** one variable per rectangular component (part)
- **Domains:** all valid **lower-left placements** `(x, y)` where the component fits on the board
  - Each placement is encoded as an **integer ID**, with a lookup map `id -> (x, y)` for decoding/printing
- **Constraints:** for every pair of components `(Pi, Pj)`, enforce **non-overlap**
  - Two axis-aligned rectangles do not overlap iff they are separated horizontally or vertically:
    - `x_i + w_i <= x_j` or `x_j + w_j <= x_i` or
    - `y_i + h_i <= y_j` or `y_j + h_j <= y_i`
  - The geometry is compiled into explicit **allowed placement pairs** (compatibility tables) for each directed arc
- **Output:** solutions can be rendered as **ASCII art** plus decoded `(x, y)` placements per component

---

## Dependencies

- **Python 3 only** (standard library; no third-party packages)

---

## Running

### Run Map-coloring problem test
```bash
python3 test_map_coloring.py
```

### Run Circuit-board layout problem test
```bash
python3 test_circuit_board.py
```
