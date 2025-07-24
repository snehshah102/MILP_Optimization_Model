from gurobipy import Model, GRB, quicksum
from data import (CENTRAL, WAREHOUSES, RETAILERS, ENTITIES, T, holding_cost,
                  ordering_cost, initial_inventory, demand, tc, lead, profiles, BIG_M, capacity, 
                emission_factors, emission_cost_weight)

def build_base_model(with_capacity_caps: bool = True, with_emissions: bool = False) -> Model:
    m = Model("PeriodicReview_sS")
    m.setParam("OutputFlag", 0)

    # Decision variables
    inv = m.addVars(ENTITIES, T, name="inv", lb=0)
    ship_w0_w = m.addVars(["W0"], WAREHOUSES, T, name="ship_w0_w", lb=0)
    ship_w_r = m.addVars(WAREHOUSES, RETAILERS, T, name="ship_w_r", lb=0)
    x_profile = m.addVars(WAREHOUSES + RETAILERS, profiles.keys(), vtype=GRB.BINARY, name="x_profile")
    x_allowed = m.addVars(WAREHOUSES + RETAILERS, T, vtype=GRB.BINARY, name="x_allowed")
    x_required = m.addVars(WAREHOUSES + RETAILERS, T, vtype=GRB.BINARY, name="x_required")
    y_order = m.addVars(WAREHOUSES + RETAILERS, T, vtype=GRB.BINARY, name="y_order")
    q = m.addVars(WAREHOUSES + RETAILERS, T, name="orderQty", lb=0)

    # (s,S) levels from Table 6
    s_level = {"W1": 480, "W2": 0, "R1": 250, "R2": 270, "R3": 360, "R4": 440}
    S_level = {"W1": 1200, "W2": 1100, "R1": 500, "R2": 630, "R3": 710, "R4": 840}

    # Objective
    transport_cost = (
        quicksum(tc["W0", w] * ship_w0_w["W0", w, t] for w in WAREHOUSES for t in T) +
        quicksum(tc[w, r] * ship_w_r[w, r, t] for w in WAREHOUSES for r in RETAILERS for t in T)
    )
    obj = (
        quicksum(ordering_cost[e]*y_order[e,t] for e in WAREHOUSES+RETAILERS for t in T)
      + quicksum(holding_cost[e]*inv[e,t]     for e in holding_cost for t in T)
      + transport_cost
    )


    if with_emissions:
        # 1) Track total emissions
        total_emissions = m.addVar(name="total_emissions", lb=0)
        # 2) Link it to all shipments
        m.addConstr(
            total_emissions
            == quicksum(emission_factors[i,j] * ship_w0_w[i,j,t]
                        for i,j in emission_factors
                        if i=="W0" and j in WAREHOUSES
                        for t in T)
             + quicksum(emission_factors[w,r] * ship_w_r[w,r,t]
                        for w,r in emission_factors
                        if w in WAREHOUSES and r in RETAILERS
                        for t in T),
            name="emissions_calc"
        )
        # 3) No hard cap any more
        #    (m.addConstr(total_emissions <= emission_budget, name="emission_cap"))
        # 4) But we *do* penalize every kg CO₂ in the objective
        obj += emission_cost_weight * total_emissions
    
    m.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance – warehouses
    for w in WAREHOUSES:
        for t in T:
            in_ship = ship_w0_w["W0", w, t - lead["W0", w]] if t - lead["W0", w] >= 1 else 0
            out_ship = quicksum(ship_w_r[w, r, t] for r in RETAILERS)
            if t == 1:
                m.addConstr(inv[w, t] == initial_inventory[w] + in_ship - out_ship, name=f"inv_bal_{w}_{t}")
            else:
                m.addConstr(inv[w, t] == inv[w, t - 1] + in_ship - out_ship, name=f"inv_bal_{w}_{t}")

    # Inventory balance – retailers
    for r in RETAILERS:
        for t in T:
            in_ship = quicksum(ship_w_r[w, r, t - lead[w, r]] if t - lead[w, r] >= 1 else 0 for w in WAREHOUSES)
            demand_t = demand[(r, t)]
            if t == 1:
                m.addConstr(inv[r, t] == initial_inventory[r] + in_ship - demand_t, name=f"inv_bal_{r}_{t}")
            else:
                m.addConstr(inv[r, t] == inv[r, t - 1] + in_ship - demand_t, name=f"inv_bal_{r}_{t}")

    # Initial and final inventory equality
    for e in WAREHOUSES + RETAILERS:
        m.addConstr(inv[e, T[-1]] == initial_inventory[e], name=f"final_inv_{e}")

    # Profile choice
    for e in WAREHOUSES + RETAILERS:
        m.addConstr(quicksum(x_profile[e, p] for p in profiles) == 1, name=f"oneProfile_{e}")
        for t in T:
            m.addConstr(x_allowed[e, t] == quicksum(profiles[p][t] * x_profile[e, p] for p in profiles), name=f"allowed_{e}_{t}")
            m.addConstr(y_order[e, t] <= x_allowed[e, t], name=f"y_leq_allowed_{e}_{t}")

    # (s,S) policy
    for e in WAREHOUSES + RETAILERS:
        for t in T:
            # Replenishment required if inventory < s
            m.addConstr(-BIG_M * x_required[e, t] + 0.0001 <= inv[e, t] - s_level[e], name=f"req1_{e}_{t}")
            m.addConstr(inv[e, t] - s_level[e] <= BIG_M * (1 - x_required[e, t]), name=f"req2_{e}_{t}")
            # Order if allowed and required
            m.addConstr(x_allowed[e, t] + x_required[e, t] <= y_order[e, t] + 1, name=f"order1_{e}_{t}")
            m.addConstr(y_order[e, t] <= x_allowed[e, t], name=f"order2_{e}_{t}")
            m.addConstr(y_order[e, t] <= x_required[e, t], name=f"order3_{e}_{t}")
            # Order quantity
            m.addConstr(q[e, t] <= BIG_M * y_order[e, t], name=f"q1_{e}_{t}")
            m.addConstr(q[e, t] >= S_level[e] - inv[e, t] - BIG_M * (1 - y_order[e, t]), name=f"q2_{e}_{t}")
            m.addConstr(q[e, t] <= S_level[e] - inv[e, t] + BIG_M * (1 - y_order[e, t]), name=f"q3_{e}_{t}")
            # Shipments
            if e in WAREHOUSES:
                m.addConstr(ship_w0_w["W0", e, t] == q[e, t], name=f"qFlow_{e}_{t}")
            else:
                m.addConstr(quicksum(ship_w_r[w, e, t] for w in WAREHOUSES) == q[e, t], name=f"qFlow_{e}_{t}")

    # Capacity extension
    if with_capacity_caps:
        for e, cap in capacity.items():
            for t in T:
                m.addConstr(inv[e, t] <= cap, name=f"cap_{e}_{t}")

    m.update()
    return m