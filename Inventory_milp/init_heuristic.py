from data import WAREHOUSES, RETAILERS, initial_inventory

s_level = {"W1": 480, "W2": 0, "R1": 250, "R2": 270, "R3": 360, "R4": 440}
S_level = {"W1": 1200, "W2": 1100, "R1": 500, "R2": 630, "R3": 710, "R4": 840}

def load_initial_solution(m):
    # Set profiles from Table 6
    profile_choices = {"W1": 6, "W2": 1, "R1": 10, "R2": 10, "R3": 10, "R4": 10}
    for e in WAREHOUSES + RETAILERS:
        p = profile_choices[e]
        v = m.getVarByName(f"x_profile[{e},{p}]")
        if v:
            v.Start = 1

    # Period-1 orders if below s
    for e in WAREHOUSES + RETAILERS:
        inv_t1 = initial_inventory[e]  # No shipments arrive in t1
        if inv_t1 < s_level[e] and profile_choices[e] == 1:  # Profile #1 allows t=1
            need = S_level[e] - inv_t1
            y = m.getVarByName(f"y_order[{e},1]")
            if y:
                y.Start = 1
            q = m.getVarByName(f"orderQty[{e},1]")
            if q:
                q.Start = need
            if e in WAREHOUSES:
                shp = m.getVarByName(f"ship_w0_w[W0,{e},1]")
                if shp:
                    shp.Start = need
            else:
                # Split across warehouses (simplified: all from W1 or W2)
                home = "W1" if e in ("R1", "R2", "R3") else "W2"
                shp = m.getVarByName(f"ship_w_r[{home},{e},1]")
                if shp:
                    shp.Start = need