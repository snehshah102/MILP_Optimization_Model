# inventory_milp/init_heuristic.py
"""Very quick constructive heuristic: assigns a simple profile, places one
early order to cover lead‑time demand, and loads .Start values to warm‑start
Gurobi.
"""
from gurobipy import Model
from data import WAREHOUSES, RETAILERS, T, profiles, demand

def load_initial_solution(m: Model) -> None:
    # --- profile choice: pick profile 6 (every 3rd period starting at t=3) for all
    for e in WAREHOUSES + RETAILERS:
        m.getVarByName(f"x_profile[{e},6]").Start = 1

    # --- order once at first allowed period to cover lead‑time demand
    for e in WAREHOUSES + RETAILERS:
        for t in T:
            if profiles[6][t]:          # period is allowed
                y = m.getVarByName(f"y_order[{e},{t}]")
                y.Start = 1
                break  # one order is enough for feasibility
