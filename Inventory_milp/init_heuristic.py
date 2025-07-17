"""
Generate a fast, always-feasible warm start for the (s,S) model.

Idea
----
• Every entity (warehouse or retailer) places a single order in period 1.
• Quantity ordered = S_level − initial_inventory, bringing stock exactly to the S value
  used in the linear (s,S) constraints.
• That single order fully specifies `orderQty`, `orderPlaced`, and the one outbound
  shipment variable that must carry the flow.
The resulting partial solution satisfies *all* balance equations, so Gurobi accepts it
as a feasible “MIP start” and can improve from there.
"""
from data import WAREHOUSES, RETAILERS, initial_inventory

def load_initial_solution(m):
    """Attach `.Start` values to variables that define a complete feasible plan."""
    # ---------- (1) choose a profile for every entity ----------
    #   We pick profile 1 (order allowed every period) for simplicity.
    for e in WAREHOUSES + RETAILERS:
        # Note: Gurobi uses a space after the comma in names
        v = m.getVarByName(f"profileChoice[{e}, 1]")
        if v:
            v.Start = 1

    # ---------- (2) set S-levels (must match model.py) ----------
    S_level = {"W1": 1600, "W2": 1500,
               "R1":  900, "R2":  950, "R3": 1000, "R4": 1050}

    # ---------- (3) period-1 orders that reach S ----------
    t0 = 1
    for e in WAREHOUSES + RETAILERS:
        need = max(0, S_level[e] - initial_inventory[e])
        if need == 0:
            continue  # already at or above S

        # Mark the binary orderPlaced[e,1] = 1
        y = m.getVarByName(f"orderPlaced[{e}, 1]")
        if y:
            y.Start = 1

        # Set the continuous orderQty[e,1] = need
        q = m.getVarByName(f"orderQty[{e}, 1]")
        if q:
            q.Start = need

        # Set the corresponding shipment variable
        if e in WAREHOUSES:
            shp = m.getVarByName(f"ship_w0_w[W0, {e}, 1]")
        else:
            home = "W1" if e in ("R1", "R2", "R3") else "W2"
            shp = m.getVarByName(f"ship_w_r[{home}, {e}, 1]")

        if shp:
            shp.Start = need