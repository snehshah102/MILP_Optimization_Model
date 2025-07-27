# PeriodicReview_sS Inventory Optimization

This project implements a periodic-review (s,S) inventory model for a multi-echelon supply chain using Gurobi. The code includes both a **base model** and an **extended model** with environmental considerations. A heuristic initializer provides warm-start solutions to accelerate convergence.

Research Paper: https://www.mdpi.com/2079-8954/13/1/33 

---

## 📂 Project Structure

```
Inventory_milp/            # Root folder
├── data.py                # All input data and model parameters
├── model.py               # Base (s,S) model builder
├── run.py                 # Entry-point: solve base & extended models
├── init_heuristic.py      # Heuristic loader for warm starts
└── README.md              # This documentation file
```

---

## 📝 data.py

* **Sets**: `CENTRAL`, `WAREHOUSES`, `RETAILERS`, `ENTITIES`, planning horizon `T`.
* **Parameters**:

  * `holding_cost`, `ordering_cost`, `initial_inventory`
  * `demand[(r,t)]` per retailer and period
  * `tc[(i,j)]`: unit transport cost between nodes
  * `lead[(i,j)]`: transport lead times
  * `profiles[p][t]`: binary ordering profiles
  * `BIG_M`: large constant for logical constraints
  * `capacity[e]`: optional capacity caps per entity, defined as:

```python
capacity = {"W1":  1200, "W2":  1200,
            "R1":  450,  "R2":  500,
            "R3":  550,  "R4":  600}
```

* *Environmental*:

  * `emission_factors[(i,j)]`: CO₂ per unit shipped
  * `emission_cost_weight`: weight (€/kg CO₂) for emissions penalty

This module centralizes all tunable inputs for easy modification.

---

## 🏗 model.py (Base Model)

Defines `build_base_model(with_capacity_caps=True)`:

1. **Decision Variables**

   * `inv[e,t]`: inventory at entity `e` in period `t`
   * `ship_w0_w["W0",w,t]`, `ship_w_r[w,r,t]`: shipment quantities
   * `(s,S)` binary logic: `x_profile`, `x_allowed`, `x_required`, `y_order`
   * `q[e,t]`: order quantity if `y_order[e,t] = 1`

2. **Objective**: Minimize

   * Setup cost: `ordering_cost * y_order`
   * Holding cost: `holding_cost * inv`
   * Transport cost: `tc * shipments`

3. **Constraints**

   * **Inventory balance** at warehouses and retailers
   * **Initial & final inventory** equality
   * **Profile enforcement**: each entity picks exactly one ordering profile
   * **(s,S) policy** logic via Big‑M constraints
   * **Shipment flows**: link orders `q[e,t]` to shipments
---

## 🌱 Extended Model (Emissions Penalty and Capacity Constraints)

Instead of a hard emissions cap, we **penalize CO₂** directly in the objective by passing `with_emissions=True`:

* **Additional variable**: `total_emissions` tracks total CO₂ across all arcs.
* **Linking constraint**: sums `emission_factors * shipments` into `total_emissions`.
* **Objective augmentation**: add `emission_cost_weight * total_emissions`.
* **Capacity limits are active** in the extended model if `with_capacity_caps=True`. This limits the capacity of each Warehouse to a certain amount

*No hard `emission_budget` constraint is applied*, so the solver balances transport & ordering cost against environmental impact.


---

## 🚀 init\_heuristic.py

Contains `load_initial_solution(model: Model)` which:

1. Computes a simple **fill-up heuristic** based on the base (s,S) targets or latest known solution.
2. **Assigns `Var.Start`** attributes on `inv`, `ship` and `q` variables.
3. Enables a **warm start** when solving the model to dramatically reduce MIP solve times.

**Usage** in `run.py`:

```python
m = build_base_model(with_capacity_caps=False)
load_initial_solution(m)
m.optimize()
```

---

## ▶ run.py (Entry‑Point)

Solves four scenarios in sequence:

1. **Base Cold‑start**: `with_capacity_caps=False`, no warm start
2. **Base Warm‑start**: same but calls `load_initial_solution`
3. **Extended Cold‑start**: `with_capacity_caps=True, with_emissions=True`
4. **Extended Warm‑start**: extended + warm start

Records and prints solve times for each.

---

## ⚙️ Installation & Requirements

* Python 3.8+
* Gurobi 9.x with academic license
* Packages: `gurobipy`, `rich`, `tabulate`

```bash
pip install gurobipy rich tabulate
```

## GenAI announcement

For our code, we used genAI to write some of the in-code comments for more clarity, as well as this README file's formatting to make it more clear and easier to read. 


