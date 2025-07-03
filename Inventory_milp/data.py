# inventory_milp/data.py
from collections import defaultdict
import pandas as pd

# ---------- Sets ----------
CENTRAL = ["W0"]                     # central warehouse
WAREHOUSES = ["W1", "W2"]
RETAILERS = ["R1", "R2", "R3", "R4"]

ENTITIES = CENTRAL + WAREHOUSES + RETAILERS
T = list(range(1, 16))               # 15-period horizon, inclusive

# ---------- Parameters ----------
# Tables 1–5 from Vicente (2025)
holding_cost = {"W1": 0.2, "W2": 0.2,
                "R1": 0.6, "R2": 0.6, "R3": 0.6, "R4": 0.6}

ordering_cost = {e: 30 for e in WAREHOUSES + RETAILERS}

initial_inventory = {"W1": 1200, "W2": 1100,
                     "R1": 350, "R2": 450, "R3": 500, "R4": 600}

demand = {("R1", t): 50 for t in T}
demand.update({("R2", t): 60 for t in T})
demand.update({("R3", t): 70 for t in T})
demand.update({("R4", t): 80 for t in T})

# unit transportation cost (Table 1)
tc = defaultdict(float)
tc.update({("W0", "W1"): 0.55, ("W0", "W2"): 0.22})
tc.update({("W1", "R1"): 0.22, ("W1", "R2"): 0.20,
           ("W1", "R3"): 0.32, ("W1", "R4"): 0.38})
tc.update({("W2", "R1"): 0.68, ("W2", "R2"): 0.52,
           ("W2", "R3"): 0.34, ("W2", "R4"): 0.10})

# lead times (Table 4) – given in “periods”
lead = defaultdict(int)
for w in WAREHOUSES:
    lead[("W0", w)] = 3
    for r in RETAILERS:
        lead[(w, r)] = 3

# replenishment profiles (Table 5) as dict: profile_id -> {t:1/0}
profiles = {}
with open(__file__.replace("data.py", "profiles.txt"), "w") as blank:
    pass  # <-- profiles hard-coded below; file reserved if you want CSV.

profiles[1] = {t: 1 for t in T}
profiles[2] = {t: int(t % 2 == 1) for t in T}             # 1,3,5,...
profiles[3] = {t: int(t % 2 == 0) for t in T}             # 2,4,6,...
profiles[4] = {t: 1 if t % 3 == 1 else 0 for t in T}      # 1,4,7,…
profiles[5] = {t: 1 if t % 3 == 2 else 0 for t in T}      # 2,5,8,…
profiles[6] = {t: 1 if t % 3 == 0 else 0 for t in T}      # 3,6,9,…
# ...continue until profile 15 exactly as the paper; abbreviated here

# ---------- Big-M ----------
BIG_M = 10_000
