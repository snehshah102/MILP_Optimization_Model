# inventory_milp/model.py

"""
Small extension implemented for the assignment:
    •   Storage‑capacity cap for every entity e and period t
            inv[e,t]  ≤  capacity[e]
        (see capacity dict in data.py)
    •   This is coded near the bottom of build_base_model().

All other files (data.py, init_heuristic.py, run.py) remain unchanged.
"""

"""Builds the base MILP (and an optional capacity‑capped extension) using Gurobi."""
from gurobipy import Model, GRB, quicksum
from data import (CENTRAL, WAREHOUSES, RETAILERS, ENTITIES,
                  T, holding_cost, ordering_cost, initial_inventory,
                  demand, tc, lead, profiles, BIG_M, capacity)

from data import *

def build_base_model() -> Model:
    # Optimize Gurobi Model
    m = Model("PeriodicReview_sS")
    m.setParam("OutputFlag", 0)   # silence solver unless you prefer verbose

    # Decision variables 
    inv = m.addVars(ENTITIES, T, name="inv", lb=0)
    ship_w0_w = m.addVars(["W0"], WAREHOUSES, T, name="ship_w0_w", lb=0)
    ship_w_r  = m.addVars(WAREHOUSES, RETAILERS, T, name="ship_w_r",  lb=0)

    # Binary vars controlling ordering policy
    x_profile = m.addVars(WAREHOUSES + RETAILERS, profiles.keys(),
                          vtype=GRB.BINARY, name="x_profile")
    x_allowed = m.addVars(WAREHOUSES + RETAILERS, T,
                          vtype=GRB.BINARY, name="x_allowed")
    y_order   = m.addVars(WAREHOUSES + RETAILERS, T,
                          vtype=GRB.BINARY, name="y_order")

    # Objective
    transport_cost = (
        quicksum(tc["W0", w] * ship_w0_w["W0", w, t]
                 for w in WAREHOUSES for t in T) +
        quicksum(tc[w, r]  * ship_w_r[w, r, t]
                 for w in WAREHOUSES for r in RETAILERS for t in T)
    )

    m.setObjective(
        quicksum(ordering_cost[e] * y_order[e, t]
                 for e in WAREHOUSES + RETAILERS for t in T)
        + quicksum(holding_cost[e] * inv[e, t]
                   for e in holding_cost for t in T)
        + transport_cost,
        GRB.MINIMIZE,
    )

    # --------- Constraints ---------
    # Inventory balance – warehouses
        # inventory balance – warehouses
    for w in WAREHOUSES:
        for t in T:
            in_ship = ship_w0_w["W0", w, t - lead["W0", w]] if t - lead["W0", w] >= 1 else 0
            out_ship = quicksum(ship_w_r[w, r, t] for r in RETAILERS)
            if t == 1:
                m.addConstr(inv[w, t] == initial_inventory[w] + in_ship - out_ship,
                             name=f"inv_bal_{w}_{t}")
            else:
                m.addConstr(inv[w, t] == inv[w, t - 1] + in_ship - out_ship,
                             name=f"inv_bal_{w}_{t}")

    # inventory balance – retailers
    for r in RETAILERS:
        for t in T:
            in_ship = quicksum(
                ship_w_r[w, r, t - lead[w, r]] if t - lead[w, r] >= 1 else 0
                for w in WAREHOUSES
            )
            demand_t = demand[(r, t)]
            if t == 1:
                m.addConstr(inv[r, t] == initial_inventory[r] + in_ship - demand_t,
                             name=f"inv_bal_{r}_{t}")
            else:
                m.addConstr(inv[r, t] == inv[r, t - 1] + in_ship - demand_t,
                             name=f"inv_bal_{r}_{t}")

    # Profile choice – exactly one profile per entity
    for e in WAREHOUSES + RETAILERS:
        m.addConstr(quicksum(x_profile[e, p] for p in profiles) == 1,
                    name=f"oneProfile_{e}")
        for t in T:
            # If profile p chosen and it allows t, then ordering allowed
            m.addConstr(
                x_allowed[e, t] ==
                quicksum(profiles[p][t] * x_profile[e, p] for p in profiles),
                name=f"allowed_{e}_{t}"
            )
            # Order can be placed only if allowed
            m.addConstr(y_order[e, t] <= x_allowed[e, t],
                        name=f"y_leq_allowed_{e}_{t}")
            
    # linear (s,S) quantity definition
    S_level = {"W1": 1600, "W2": 1500,
               "R1": 900,  "R2": 950, "R3": 1000, "R4": 1050}

    q = m.addVars(WAREHOUSES + RETAILERS, T, name="orderQty", lb=0)

    for e in WAREHOUSES + RETAILERS:
        for t in T:
            # link q with y_order via a Big-M
            m.addConstr(q[e, t] <= BIG_M * y_order[e, t], name=f"qBigM1_{e}_{t}")
            # ensure inventory jumps to S when an order is placed
            m.addConstr(inv[e, t] + q[e, t] >= S_level[e] - BIG_M * (1 - y_order[e, t]),
                        name=f"qBigM2_{e}_{t}")
            # outbound shipments equal q
            if e in WAREHOUSES:
                m.addConstr(ship_w0_w["W0", e, t] == q[e, t], name=f"qFlow_{e}_{t}")
            else:  # retailer
                home = "W1" if e in ["R1", "R2", "R3"] else "W2"
                m.addConstr(ship_w_r[home, e, t] == q[e, t], name=f"qFlow_{e}_{t}")

    # optional capacity caps (small extension)
    for e, cap in capacity.items():
        for t in T:
            m.addConstr(inv[e, t] <= cap, name=f"cap_{e}_{t}")
    m.update()
    return m
