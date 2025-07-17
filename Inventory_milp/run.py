"""
Entry-point script:
* Builds the MILP once (with capacity-caps extension already inside).
* Solves twice — cold start vs. warm start.
* Prints solve times side-by-side.
"""

import time
from rich import print
from tabulate import tabulate

from model import build_base_model
from init_heuristic import load_initial_solution

# helper: solve & time
def time_solve(model, label: str) -> float:
    """
    Optimize a Gurobi model and return elapsed wall-clock time (seconds).
    """
    t0 = time.perf_counter()
    model.optimize()
    elapsed = time.perf_counter() - t0

    status = model.Status            # 2 == OPTIMAL
    obj = model.ObjVal if status == 2 else float("nan")
    gap = model.MIPGap if status == 2 else float("nan")

    print(f"[bold cyan]{label}[/]  status={status}  "
          f"obj={obj:.2f}  gap={gap:.4f}  time={elapsed:.2f}s")
    return elapsed

def main() -> None:
    rows = []

    # 1) Cold start (Gurobi’s own default (none))
    m_cold = build_base_model()
    t_cold = time_solve(m_cold, "Cold-start")
    rows.append(("cold", f"{t_cold:.2f}"))

    # 2) Warm start (The heuristic we injected (init_heuristic.py))
    m_warm = build_base_model()
    load_initial_solution(m_warm)
    t_warm = time_solve(m_warm, "Warm-start")
    rows.append(("warm", f"{t_warm:.2f}"))

    # summary table
    print("\n[bold]Solve-time comparison (seconds)[/]")
    print(tabulate(rows, headers=["Init", "Time"], tablefmt="github"))


if __name__ == "__main__":
    main()