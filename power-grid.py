from gurobipy import Model, GRB, quicksum

# Data
plants = [0, 1, 2]  # Power plants
cities = [0, 1, 2]  # Cities

# Fixed costs for plants (dollars per day)
f = [5000, 4000, 3000]

# Variable generation costs (dollars per MW)
v = [20, 25, 15]  # Cost per unit of power generated

# Generation capacities (MW per day)
C = [100, 120, 150]

# Demand at each city (MW/day) , the sum of them have to be <= sum of capacities
d = [80, 70, 60]

# Transmission costs (per MW , logically they should be less than half of the cost per unit )
c = [
    [8, 6, 10],  # From plant 0 to cities
    [9, 7, 4],   # From plant 1 to cities
    [14, 5, 6]   # From plant 2 to cities
]

# Transmission capacities per day (keep them high to ensure that an optimal solution exist , each one have to be higher than half the demand 
# of the respective city)
T = [
    [50, 60, 70],
    [40, 80, 90],
    [100, 70, 50]
]



# Transmission losses (between 0 and 0.05 at most)
L = [
    [0.02, 0.03, 0.01],
    [0.01, 0.02, 0.03],
    [0.03, 0.01, 0.02]
]

# Create the model
model = Model("PowerGridOptimization")

# Decision variables
x = model.addVars(plants, cities, name="x", vtype=GRB.CONTINUOUS, lb=0)  # Power transmitted
g = model.addVars(plants, name="g", vtype=GRB.CONTINUOUS, lb=0)          # Power generated
y = model.addVars(plants, name="y", vtype=GRB.BINARY)                   # Plant operational

# Objective function: Minimize total cost
model.setObjective(
    quicksum(f[i] * y[i] for i in plants) +               # Fixed costs
    quicksum(v[i] * g[i] for i in plants) +               # Variable generation costs
    quicksum(c[i][j] * x[i, j] for i in plants for j in cities),  # Transmission costs
    GRB.MINIMIZE
)

# Constraints

# 1. Demand satisfaction at each city
for j in cities:
    model.addConstr(
        quicksum((1 - L[i][j]) * x[i, j] for i in plants) >= d[j],
        name=f"demand_{j}"
    )

# 2. Power balance at each plant
for i in plants:
    model.addConstr(
        quicksum(x[i, j] for j in cities) <= g[i],
        name=f"balance_{i}"
    )

# 3. Generation capacity
for i in plants:
    model.addConstr(
        g[i] <= C[i] * y[i],
        name=f"capacity_{i}"
    )

# 4. Transmission capacity
for i in plants:
    for j in cities:
        model.addConstr(
            x[i, j] <= T[i][j],
            name=f"transmission_{i}_{j}"
        )

# 5. Binary constraint is already handled by the vtype of y

# Optimize the model
model.optimize()

# Output the results
# In the case of multiple solutions gurobi will show only one , for the rest of the solutions use the PoolSearchMode
if model.status == GRB.OPTIMAL:
    print(f"Optimal total cost: {model.objVal}")
    for i in plants:
        print(f"Plant {i}: Operational = {y[i].x}, Power generated = {g[i].x}")
        for j in cities:
            print(f"  Power transmitted to City {j}: {x[i, j].x}")
# if no optimals are found (model.status==GRB.INFEASIBLE , no solution satisfies all the constaints )you can use model.computeIIS() to 
# identify conflicting constraints
else:
    print("No optimal solution found.")
