import pyomo.environ as pyomo
import numpy as np
import pandas as pd


def build_model(streams, costs, ad_yield_data, rf_yield_data, cc_srds_yield_data, cc_srfo_yield_data):
    model = pyomo.ConcreteModel()
    model.x = pyomo.Var(streams, domain=pyomo.NonNegativeReals)
    # model.cost = pyomo.Objective(expr = sum(model.x[c] * costs[c]['cost'] for c in costs))
    model.obj = pyomo.Objective(expr = model.x['14'] + model.x['16'] + model.x['17'], sense=pyomo.maximize)
    model.x['1'].value = 100000
    model.x['1'].fixed = True

    model.splitA = pyomo.Constraint(expr = model.x['3'] == model.x['18'] + model.x['19'])
    model.splitB = pyomo.Constraint(expr = model.x['4'] == model.x['8'] + model.x['9'])
    model.splitC = pyomo.Constraint(expr = model.x['5'] == model.x['10'] + model.x['11'])
    model.splitD = pyomo.Constraint(expr = model.x['6'] == model.x['12'] + model.x['13'])
    model.splitE = pyomo.Constraint(expr = model.x['14'] == model.x['20'] + model.x['21'])
    model.splitF = pyomo.Constraint(expr = model.x['9'] == model.x['22'] + model.x['23'] + model.x['24'])
    model.splitG = pyomo.Constraint(expr = model.x['16'] == model.x['25'] + model.x['26'])
    model.splitH = pyomo.Constraint(expr = model.x['17'] == model.x['27'] + model.x['28'])
    model.splitI = pyomo.Constraint(expr = model.x['11'] == model.x['29'] + model.x['30'])
    model.splitJ = pyomo.Constraint(expr = model.x['13'] == model.x['31'] + model.x['32'])

    model.pg_blend = pyomo.Constraint(expr = model.x['33'] == model.x['18'] + model.x['20'] + model.x['22'] + model.x['25'])
    model.rg_blend = pyomo.Constraint(expr = model.x['34'] == model.x['19'] + model.x['21'] + model.x['23'] + model.x['26'])
    model.df_blend = pyomo.Constraint(expr = model.x['35'] == model.x['24'] + model.x['27'] + model.x['29'] + model.x['31'])
    model.fo_blend = pyomo.Constraint(expr = model.x['36'] == model.x['28'] + model.x['30'] + model.x['32'])

    model.ad_yield = pyomo.ConstraintList()
    for y in ad_yield_data:
        model.ad_yield.add(expr = model.x[y] == model.x['1'] * ad_yield_data[y]['yield'])

    model.rf_yield = pyomo.ConstraintList()
    for y in rf_yield_data:
        model.rf_yield.add(expr = model.x[y] == model.x['8'] * rf_yield_data[y]['yield'])

    model.cc_yield = pyomo.ConstraintList()
    for y in cc_srds_yield_data:
        model.cc_yield.add(expr = model.x[y] == model.x['10'] * cc_srds_yield_data[y]['yield'] + model.x['12'] * cc_srfo_yield_data[y]['yield'])

    return model



def execute_optimization():
    streams = [str(x) for x in range(1, 37, 1)]
    costs = {
        '1': {'cost': -33},
        '2': {'cost': 0.01965},
        '7': {'cost': 0.01965},
        '8': {'cost': -2.5},
        '10': {'cost': -2.2},
        '12': {'cost': -2.2},
        '15': {'cost': 0.01965},
        '33': {'cost': 45.36},
        '34': {'cost': 43.68},
        '35': {'cost': 40.32},
        '36': {'cost': 13.14}
    }
    ad_yields = {
        '2': {'yield': 35.42},
        '3': {'yield': 0.270},
        '4': {'yield': 0.237},
        '5': {'yield': 0.087},
        '6': {'yield': 0.372}
    }
    rf_yields = {
        '7': {'yield': 158.7},
        '14': {'yield': 0.928}
    }
    cc_srds_yields = {
        '15': {'yield': 336.9},
        '16': {'yield': 0.619},
        '17': {'yield': 0.189}
    }
    cc_srfo_yields = {
        '15': {'yield': 386.4},
        '16': {'yield': 0.688},
        '17': {'yield': 0.220}
    }
    opt_model = build_model(streams, costs, ad_yields, rf_yields, cc_srds_yields, cc_srfo_yields)

    solver = pyomo.SolverFactory('glpk')
    solver.solve(opt_model)
    for c in streams:
        print(opt_model.x[c])
        print(opt_model.x[c]())


def test_opt():
    data = {
        'A': {'abv': 0.045, 'cost': 0.32},
        'B': {'abv': 0.037, 'cost': 0.25},
        'W': {'abv': 0.000, 'cost': 0.05},
    }
    vol = 100
    abv = 0.040

    C = data.keys()
    model = pyomo.ConcreteModel()
    model.x = pyomo.Var(C, domain=pyomo.NonNegativeReals)
    model.cost = pyomo.Objective(expr=sum(model.x[c] * data[c]['cost'] for c in C))
    model.vol = pyomo.Constraint(expr=vol == sum(model.x[c] for c in C))
    model.abv = pyomo.Constraint(expr=0 == sum(model.x[c] * (data[c]['abv'] - abv) for c in C))

    solver = pyomo.SolverFactory('glpk')
    solver.solve(model)

    print('Optimal Blend')
    for c in data.keys():
        print('  ', c, ':', model.x[c](), 'gallons')
    print()
    print('Volume = ', model.vol(), 'gallons')
    print('Cost = $', model.cost())



def main():
    result = execute_optimization()


if __name__ == "__main__":
    main()