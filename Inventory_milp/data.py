from collections import defaultdict

# Sets
CENTRAL = ["W0"]                     # supply node (infinite stock)
WAREHOUSES = ["W1", "W2"]
RETAILERS = ["R1", "R2", "R3", "R4"]
ENTITIES = CENTRAL + WAREHOUSES + RETAILERS

# 15‑period planning horizon
T = list(range(1, 16))

# Parameters
# Holding cost per unit per period
holding_cost = {"W1": 0.20, "W2": 0.20,
                "R1": 0.60, "R2": 0.60, "R3": 0.60, "R4": 0.60}

# Fixed ordering (setup) cost
ordering_cost = {e: 30 for e in WAREHOUSES + RETAILERS}

# Initial inventory
initial_inventory = {"W1": 1_200, "W2": 1_100,
                     "R1": 350, "R2": 450, "R3": 500, "R4": 600}

# Retail demands (constant each period for simplicity – edit as needed)
demand = {("R1", t): 50 for t in T}
demand.update({("R2", t): 60 for t in T})
demand.update({("R3", t): 70 for t in T})
demand.update({("R4", t): 80 for t in T})

# Unit transportation cost
tc = defaultdict(float)
tc.update({("W0", "W1"): 0.55, ("W0", "W2"): 0.22})
tc.update({("W1", "R1"): 0.22, ("W1", "R2"): 0.20,
           ("W1", "R3"): 0.32, ("W1", "R4"): 0.38})
tc.update({("W2", "R1"): 0.68, ("W2", "R2"): 0.52,
           ("W2", "R3"): 0.34, ("W2", "R4"): 0.10})

# Transport lead times (periods)
lead = defaultdict(int)
for w in WAREHOUSES:
    lead[("W0", w)] = 3
    for r in RETAILERS:
        lead[(w, r)] = 3

# Replenishment‑profile matrix 
# profiles[p][t] == 1 if profile p allows orders in period t
profiles = {}
# p1 = order every period
profiles[1] = {t: 1 for t in T}
# p2 = odd periods
profiles[2] = {t: int(t % 2 == 1) for t in T}
# p3 = even periods
profiles[3] = {t: int(t % 2 == 0) for t in T}
# p4/p5/p6 = 3‑cycle starting at 1/2/3
profiles[4] = {t: 1 if t % 3 == 1 else 0 for t in T}
profiles[5] = {t: 1 if t % 3 == 2 else 0 for t in T}
profiles[6] = {t: 1 if t % 3 == 0 else 0 for t in T}
profiles[7]  = {t: 1 if (t-1) % 4 == 0 else 0 for t in T}   # 1,5,9,13
profiles[8]  = {t: 1 if (t-2) % 4 == 0 else 0 for t in T}   # 2,6,10,14
profiles[9]  = {t: 1 if (t-3) % 4 == 0 else 0 for t in T}   # 3,7,11,15
profiles[10] = {t: 1 if  t      % 4 == 0 else 0 for t in T} # 4,8,12
profiles[11] = {t: 1 if (t-1) % 5 == 0 else 0 for t in T}   # 1,6,11
profiles[12] = {t: 1 if (t-2) % 5 == 0 else 0 for t in T}   # 2,7,12
profiles[13] = {t: 1 if (t-3) % 5 == 0 else 0 for t in T}   # 3,8,13
profiles[14] = {t: 1 if (t-4) % 5 == 0 else 0 for t in T}   # 4,9,14
profiles[15] = {t: 1 if  t      % 5 == 0 else 0 for t in T} # 5,10,15

# Big‑M (sufficiently large)
BIG_M = 10_000

capacity = {"W1":  900, "W2":  850,
            "R1":  450, "R2":  500,
            "R3":  550, "R4":  600}
