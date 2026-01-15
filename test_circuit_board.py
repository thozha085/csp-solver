# Name: Thomas Zhang
# Date: 12 November 2025
# Project: CSP

from __future__ import annotations

from solver import backtracking_search
from circuit_board import build_board_csp, render_ascii, example_from_prompt

"""
Solve the circuit-board layout for the example in the instructions and
print an ASCII layout.

Run:
python3 test_circuit_board.py
"""

def main():
    W, H, parts = example_from_prompt()
    csp, enc = build_board_csp(W, H, parts)

    # Try a reasonably strong combo - fall back to plain on failure.
    sol = backtracking_search(csp.copy_with_domains(), variable_strategy="mrv+degree", use_lcv=True, inference="ac3")
    if not sol:
        sol = backtracking_search(csp.copy_with_domains(), variable_strategy="none", use_lcv=False, inference="none")

    if sol:
        print(f"Found layout on {W}x{H} board:\n")
        print(render_ascii(W, H, parts, sol, enc))
        print("\nVariable assignments (var -> (x,y)):")
        # Pretty-print positions for clarity
        from circuit_board import decode_solution_positions
        pos = decode_solution_positions(enc, sol)
        for i in sorted(pos):
            print(f" v{i}({parts[i].name}): {pos[i]}")
    else:
        print("No layout found (instance appears unsatisfiable).")

if __name__ == "__main__":
    main()