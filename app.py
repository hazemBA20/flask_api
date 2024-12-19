from flask import Flask , request , render_template , jsonify

from gurobipy import Model, GRB, quicksum

app=Flask(__name__)


@app.route('/test', methods=['POST' , 'GET'])

def receive_json():
  global json_array
  if request.method=="POST":
    
    data=request.get_json()
    cities1 = [
      {
          "id": city["id"],
          "name": city["name"],
          "demand": city["demand"]
      }
    for city in data["cities"]
    
  ]
    
    

    powerplants = [
      {
          "id": plant["id"],
          "name": plant["name"],
          "capacity": plant["capacity"],
          "fixedCost": plant["fixedCost"],
          "dynamicCost": plant["dynamicCost"]
      }
    for plant in data["powerplants"]
  ]

    c = data["transmission cost per unit"]
    T = data["transmission capacities"]
    L= data["transmission loss"]
    plants = [plant["id"] for plant in powerplants]
    cities = [city["id"] for city in cities1]
    print(plants)
    print(cities)
    print(f"Transmission cost per unit: {c}")
    print(f"Transmission capacities: {T}")
    print(f"Transmission loss: {L}")
   
    # Fixed costs for plants (dollars per day)
    f = [x["fixedCost"] for x in powerplants ]
    # Variable generation costs (dollars per MW)
    v = [x["dynamicCost"]for x in powerplants] # Cost per unit of power generated
    # Generation capacities (MW per day)
    C = [x["capacity"] for x in powerplants]
    # Demand at each city (MW/day) , the sum of them have to be <= sum of capacities
    d = [x["demand"] for x in cities1]
    # Create the model
    print(f)
    print(v)
    print(C)
    print("demand",d)
    model = Model("PowerGridOptimization")

    # Decision variables
    x = model.addVars(plants, cities, name="x", vtype=GRB.CONTINUOUS, lb=0)  # Power transmitted
    g = model.addVars(plants, name="g", vtype=GRB.CONTINUOUS, lb=0)          # Power generated
    y = model.addVars(plants, name="y", vtype=GRB.BINARY)                   # Plant operational

    # Objective function: Minimize total cost
    if f[0]:
        model.setObjective(
            quicksum(f[i] * y[i] for i in plants) +               # Fixed costs
            quicksum(v[i] * g[i] for i in plants) +               # Variable generation costs
            quicksum(c[i][j] * x[i, j] for i in plants for j in cities),  # Transmission costs
            GRB.MINIMIZE
        )
    else:
        model.setObjective(
            quicksum(v[i] * g[i] for i in plants) +               # Variable generation costs
            quicksum(c[i][j] * x[i, j] for i in plants for j in cities),  # Transmission costs
            GRB.MINIMIZE
        )

    # Constraints

    # 1. Demand satisfaction at each city
    if L :
        print("============>1.1")
        for j in cities:
            model.addConstr(
                quicksum((1 - L[i][j]) * x[i, j] for i in plants) >= d[j],
                name=f"demand_{j}"
            )
    else:
        print("============>1.2")
        for j in cities:
            model.addConstr(
                quicksum(x[i, j] for i in plants) >= d[j],
                name=f"demand_{j}"
            )


    # 2. Power balance at each plant
    for i in plants:
        print("====================> 2")
        model.addConstr(
            quicksum(x[i, j] for j in cities) <= g[i],
            name=f"balance_{i}"
        )

    # 3. Generation capacity
    if C[0]:
        print("====================> 3")
        for i in plants:
            model.addConstr(
                g[i] <= C[i] * y[i],
                name=f"capacity_{i}"
            )

    # 4. Transmission capacity
    if T:
        print("====================> 4")
        for i in plants:
            for j in cities:
                model.addConstr(
                    x[i, j] <= T[i][j],
                    name=f"transmission_{i}_{j}"
                )

    if C[0]:
        print("====================> 5")
        for i in plants:
            model.addConstr(
                g[i] <= C[i] * y[i],
                name=f"capacity_{i}"
            )

    # 5. Binary constraint is already handled by the vtype of y

    # Optimize the model
    model.optimize()

    # Output the results
    state=[]
    generated=[]
    tmp=[]
    power=[]
    # In the case of multiple solutions gurobi will show only one , for the rest of the solutions use the PoolSearchMode
    if model.status == GRB.OPTIMAL:
        print(f"Optimal total cost: {model.objVal}")
        for i in plants:
            print(f"Plant {i}: Operational = {y[i].x}, Power generated = {g[i].x}")
            state.append(y[i].x)
            generated.append(g[i].x)
            for j in cities:
                print(f"  Power transmitted to City {j}: {x[i, j].x}")
                tmp.append(x[i, j].x)
            power.append(tmp)    
            tmp=[]
        json_array = [
        {
            "state": state[i],
            "generated": generated[i],
            "power": power[i]
        }
        for i in range(len(state))
                            ]
        print(json_array)
        return json_array
                
    # if no optimals are found (model.status==GRB.INFEASIBLE , no solution satisfies all the constaints )you can use model.computeIIS() to 
    # identify conflicting constraints
    else:
        print("No optimal solution found.")
        model.computeIIS()

        print("\nConflicting constraints:")
        for constr in model.getConstrs():
            if constr.IISConstr:
                print(f"- {constr.ConstrName}")
  if request.method=="GET":
    return json_array

if __name__=="__main__":
  
  app.run(debug=True)
