# inventory_milp/model.py
"""Builds the base MILP (and an optional capacity‑capped extension) using Gurobi."""
from gurobipy import Model, GRB, quicksum
from data import (CENTRAL, WAREHOUSES, RETAILERS, ENTITIES,
                  T, holding_cost, ordering_cost, initial_inventory,
                  demand, tc, lead, profiles, BIG_M)

def build_base_model(capacity: dict | None = None) -> Model:
    """Return a ready‑to‑optimize Gurobi model.

    Args
    ----
    capacity : dict | None
        Optional {entity: max_units} upper bound on inventory.  If provided,
        a single extra constraint per (entity, t) is added (our ‘small
        extension’ to the original paper).
    """
    m = Model("PeriodicReview_sS")
    m.setParam("OutputFlag", 0)   # silence solver unless you prefer verbose

    # --------- Decision variables ---------
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

    # --------- Objective ---------
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
    for w in WAREHOUSES:
        for t in T:
            received = (
                ship_w0_w["W0", w, t - lead["W0", w]]
                if t - lead["W0", w] >= 1 else 0
            )
            shipped = quicksum(ship_w_r[w, r, t] for r in RETAILERS)
            if t == 1:
                m.addConstr(inv[w, t] ==
                            initial_inventory[w] + received - shipped,
                            name=f"invBal_{w}_{t}")
            else:
                m.addConstr(inv[w, t] ==
                            inv[w, t-1] + received - shipped,
                            name=f"invBal_{w}_{t}")

    # Inventory balance – retailers
    for r in RETAILERS:
        for t in T:
            received = quicksum(
                ship_w_r[w, r, t - lead[w, r]] if t - lead[w, r] >= 1 else 0
                for w in WAREHOUSES)
            if t == 1:
                m.addConstr(inv[r, t] ==
                            initial_inventory[r] + received - demand[r, t],
                            name=f"invBal_{r}_{t}")
            else:
                m.addConstr(inv[r, t] ==
                            inv[r, t-1] + received - demand[r, t],
                            name=f"invBal_{r}_{t}")

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

    # --------- Small extension – inventory capacity ---------
    if capacity:
        for e, cap in capacity.items():
            for t in T:
                m.addConstr(inv[e, t] <= cap, name=f"cap_{e}_{t}")

    m.update()
    return m
