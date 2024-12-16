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
    plants = [0, 1]  # Power plants
    cities = [0, 1, 2]  # Cities
   
    # Fixed costs for plants (dollars per day)
    f = [x["fixedCost"] for x in powerplants ]
    # Variable generation costs (dollars per MW)
    v = [x["dynamicCost"]for x in powerplants] # Cost per unit of power generated
    # Generation capacities (MW per day)
    C = [x["capacity"] for x in powerplants]
    # Demand at each city (MW/day) , the sum of them have to be <= sum of capacities
    d = [x["demand"] for x in cities1]
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
                
    # if no optimals are found (model.status==GRB.INFEASIBLE , no solution satisfies all the constaints )you can use model.computeIIS() to 
    # identify conflicting constraints
    else:
        print("No optimal solution found.")


  
    return json_array
  if request.method=="GET":
    return json_array

      
   

  

 

if __name__=="__main__":
  
  app.run(debug=True)
