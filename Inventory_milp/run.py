# inventory_milp/run.py
"""CLI entry‑point: solves base vs capacity‑capped models with and without warm‑starts,
then prints a timing table.
"""
import time
from tabulate import tabulate

from model import build_base_model
from init_heuristic import load_initial_solution
from data import WAREHOUSES, RETAILERS

def solve_and_time(model, label):
    t0 = time.perf_counter()
    model.optimize()
    dt = time.perf_counter() - t0
    obj = model.ObjVal if model.Status == 2 else None
    print(f"[bold cyan]{label}[/]   status={model.Status}   obj={obj}   time={dt:.2f}s")
    return dt

def main():
    results = []

    # --- cold base ---
    m1 = build_base_model()
    t1 = solve_and_time(m1, "Cold‑start base")

    # --- warm base ---
    m2 = build_base_model()
    load_initial_solution(m2)
    t2 = solve_and_time(m2, "Warm‑start base")

    # --- cold extended (capacity caps) ---
    caps = {e: 1500 for e in WAREHOUSES} | {e: 900 for e in RETAILERS}
    m3 = build_base_model(capacity=caps)
    t3 = solve_and_time(m3, "Cold‑start extended")

    # --- warm extended ---
    m4 = build_base_model(capacity=caps)
    load_initial_solution(m4)
    t4 = solve_and_time(m4, "Warm‑start extended")

    table = [["base", "cold", f"{t1:.2f}"],
             ["base", "warm", f"{t2:.2f}"],
             ["extended", "cold", f"{t3:.2f}"],
             ["extended", "warm", f"{t4:.2f}"]]
    print("\n[bold]Solve‑time comparison (s)[/]")
    print(tabulate(table, headers=["model", "init", "time"], tablefmt="github"))

if __name__ == "__main__":
    main()
