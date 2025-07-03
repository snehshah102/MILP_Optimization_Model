# inventory_milp/run.py
import time, sys
from Inventory_milp.model import build_base_model
from Inventory_milp.init_heuristic import load_initial_solution
from Inventory_milp.data import WAREHOUSES, RETAILERS
from tabulate import tabulate

def time_solve(model, label):
    t0 = time.perf_counter()
    model.optimize()
    dt = time.perf_counter() - t0
    gap = model.MIPGap if model.Status == 2 else None
    print(f"[bold cyan]{label}[/]  status={model.Status}  "
          f"obj={model.ObjVal:,.2f}  gap={gap:.4f}  time={dt:.2f}s")
    return dt

def main():
    results = []

    # ---- (1) cold base model ----
    m1 = build_base_model()
    t1 = time_solve(m1, "Cold-start  base")

    # ---- (2) warm base model ----
    m2 = build_base_model()
    load_initial_solution(m2)
    t2 = time_solve(m2, "Warm-start base")

    # ---- (3) cold extended (capacity caps) ----
    caps = {e: 1500 for e in WAREHOUSES} | {e: 900 for e in RETAILERS}
    m3 = build_base_model(capacity=caps)
    t3 = time_solve(m3, "Cold-start  extended")

    # ---- (4) warm extended ----
    m4 = build_base_model(capacity=caps)
    load_initial_solution(m4)
    t4 = time_solve(m4, "Warm-start extended")

    # ---- summary table ----
    rows = [["Base", "cold", f"{t1:.2f}"],
            ["Base", "warm", f"{t2:.2f}"],
            ["Extended", "cold", f"{t3:.2f}"],
            ["Extended", "warm", f"{t4:.2f}"]]
    print("\n[bold]Solve-time comparison (seconds)[/]")
    print(tabulate(rows, headers=["Model", "Init", "Time"], tablefmt="github"))

if __name__ == "__main__":
    main()
