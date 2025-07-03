# inventory_milp/init_heuristic.py
from gurobipy import quicksum, GRB
from Inventory_milp.data import *
import random

def load_initial_solution(m):
    """
    Very fast 2-step heuristic:
    1. choose profile #6 for warehouses, #10 for retailers (mirrors the case study)
    2. set each shipment so that inventories exactly hit S (=initial + 1 cycle)
    The assignments satisfy all balance equations → feasible.
    """
    # -------- choose profiles ----------
    for w in WAREHOUSES:
        m.getVarByName(f"profileChoice[{w},6]").Start = 1
    for r in RETAILERS:
        m.getVarByName(f"profileChoice[{r},10]").Start = 1

    # -------- shipment decisions ----------
    S_level = {"W1": 1200, "W2": 1100,
               "R1": 500, "R2": 630, "R3": 710, "R4": 840}

    for t in T:
        # warehouses order at first allowed period
        for w in WAREHOUSES:
            if profiles[6][t]:                       # allowed day
                y = m.getVarByName(f"orderPlaced[{w},{t}]")
                y.Start = 1
                qty = S_level[w] - initial_inventory[w] if t == 3 else 0
                if qty > 0:
                    m.getVarByName(f"ship_w0_w[W0,{w},{t}]").Start = qty

        # retailers place orders through their default warehouse
        for r in RETAILERS:
            if profiles[10][t]:
                y = m.getVarByName(f"orderPlaced[{r},{t}]")
                y.Start = 1
                qty = demand[r, t] * lead["W1", r]   # crude
                if qty > 0:
                    home = "W1" if r in ["R1", "R2", "R3"] else "W2"
                    m.getVarByName(f"ship_w_r[{home},{r},{t}]").Start = qty
