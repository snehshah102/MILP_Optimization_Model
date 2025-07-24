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
from gurobipy import GRB

# helper: solve & time
def time_solve(model, label: str) -> float:
    """
    Optimize a Gurobi model and return elapsed wall-clock time (seconds).
    """
    t0 = time.perf_counter()
    model.optimize()
    if model.Status == GRB.INFEASIBLE:
        model.computeIIS()
        model.write("model_iis.ilp")
        for c in model.getConstrs():
            if c.IISConstr:
                print("IIS constraint:", c.ConstrName)
    elapsed = time.perf_counter() - t0

    status = model.Status            # 2 == OPTIMAL
    obj = model.ObjVal if status == 2 else float("nan")
    gap = model.MIPGap if status == 2 else float("nan")

    print(f"[bold cyan]{label}[/]  status={status}  "
          f"obj={obj:.2f}  gap={gap:.4f}  time={elapsed:.2f}s")
    return elapsed

def main() -> None:
    rows = []

    # 1) Base model (no capacity caps)
    m_base_cold = build_base_model(with_capacity_caps=False)
    t_base_cold = time_solve(m_base_cold, "Base Cold-start")
    rows.append(("base", "cold", f"{t_base_cold:.2f}"))

    m_base_warm = build_base_model(with_capacity_caps=False)
    load_initial_solution(m_base_warm)
    t_base_warm = time_solve(m_base_warm, "Base Warm-start")
    rows.append(("base", "warm", f"{t_base_warm:.2f}"))

    # 2) Extended model (with capacity caps)
    m_ext_cold = build_base_model(with_capacity_caps=True, with_emissions=True)
    t_ext_cold = time_solve(m_ext_cold, "Extended Cold-start")
    rows.append(("extended", "cold", f"{t_ext_cold:.2f}"))

    m_ext_warm = build_base_model(with_capacity_caps=True, with_emissions=True)
    load_initial_solution(m_ext_warm)
    t_ext_warm = time_solve(m_ext_warm, "Extended Warm-start")
    rows.append(("extended", "warm", f"{t_ext_warm:.2f}"))

    # summary table
    print("\n[bold]Solve-time comparison (seconds)[/]")
    print(tabulate(rows, headers=["Model", "Init", "Time"], tablefmt="github"))


if __name__ == "__main__":
    main()