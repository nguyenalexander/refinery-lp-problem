import pyomo.environ as pyomo
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def execute_optimization(opt_model):
    """
    A helper function to receive the instantiated Pyomo Model then solve the optimization problem. Returns the solved model object.
    """
    # e.g. Shutting down reformer for period 4
    # opt_model.x['srn', 'srn_tk', 'rf', 4].fix(0)
    # opt_model.x['srn', 'srn_sp', 'rf', 4].fix(0)

    # Display instance information
    opt_model.pprint()

    solver = pyomo.SolverFactory('glpk')
    solver.solve(opt_model, tee=True)

    return opt_model


def print_output(opt_model):
    """
    A helper function to print the flow rates, then the total profit and production of each product and their properties..
    """
    opt_model.display()
    print('Objective Excluding Tank Holding Costs:', sum(pyomo.value(opt_model.x[c, t] * opt_model.costs[c]) for c in opt_model.costs for t in opt_model.timeperiods))
    print('Tank Holding Costs:', sum(opt_model.tank_holding_cost[tank] * pyomo.value(opt_model.m[tank, t]) for tank in opt_model.tank_set for t in opt_model.timeperiods))

    for t in opt_model.timeperiods:
        print('~~~~~~~~~~~~~ Timeperiod :', t, ' ~~~~~~~~~~~~~')
        print('PG Octane:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.pg_octane_rating[mat, uout, uin]) for (mat, uout, uin) in opt_model.pg_set) / pyomo.value(opt_model.x['pg_prod', 'pg_tk', 'pg_out', t]))
        print('PG Vapour Pressure:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.pg_vpress_rating[mat, uout, uin]) for (mat, uout, uin) in opt_model.pg_set) / pyomo.value(opt_model.x['pg_prod', 'pg_tk', 'pg_out', t]))
        print('RG Octane:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.rg_octane_rating[mat, uout, uin]) for (mat, uout, uin) in opt_model.rg_set) / pyomo.value(opt_model.x['rg_prod', 'rg_tk', 'rg_out', t]))
        print('RG Vapour Pressure:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.rg_vpress_rating[mat, uout, uin]) for (mat, uout, uin) in opt_model.rg_set) / pyomo.value(opt_model.x['rg_prod', 'rg_tk', 'rg_out', t]))
        print('DF Density:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.df_density_spec[mat, uout, uin]) for (mat, uout, uin) in opt_model.df_set) / pyomo.value(opt_model.x['df_prod', 'df_tk', 'df_out', t]))
        print('DF Sulfur:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.df_sulfur_spec[mat, uout, uin]) for (mat, uout, uin) in opt_model.df_set) / pyomo.value(opt_model.x['df_prod', 'df_tk', 'df_out', t]))
        print('FO Density:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.fo_density_spec[mat, uout, uin]) for (mat, uout, uin) in opt_model.fo_set) / pyomo.value(opt_model.x['fo_prod', 'fo_tk', 'fo_out', t]))
        print('FO Sulfur:', sum(pyomo.value(opt_model.x[mat, uout, uin, t]) * pyomo.value(opt_model.fo_sulfur_spec[mat, uout, uin]) for (mat, uout, uin) in opt_model.fo_set) / pyomo.value(opt_model.x['fo_prod', 'fo_tk', 'fo_out', t]))


def store_results_pd(opt_model, solver_information):
    """
    A helper function to store the optimization results in a dataframe.
    """
    store_index = []
    store_values = []

    # Store flow rates and tank volumes
    for v in opt_model.component_data_objects(pyomo.Var):
        store_index.append(v.name)
        store_values.append(pyomo.value(v))

    # Store Alphas
    for p in opt_model.component_data_objects(pyomo.Param):
        if hasattr(p, 'name'):
            if 'alpha' in p.name:
                store_index.append(p.name)
                store_values.append(pyomo.value(p))

    # Sort by alphabetical
    paired_list = zip(store_index, store_values)
    sorted_list = sorted(paired_list)
    tuples_list = zip(*sorted_list)
    store_index, store_values = [list(i) for i in tuples_list]

    # Add objective value to top
    for obj in opt_model.component_data_objects(pyomo.Objective):
        store_index.insert(0, 'Objective')
        store_values.insert(0, pyomo.value(obj))

    store_index.insert(0, 'Termination Condition')
    store_values.insert(0, solver_information.solver.termination_condition)
    store_index.insert(0, 'Solver Status')
    store_values.insert(0, solver_information.solver.status)

    output_df = pd.Series(data=store_values, index=store_index)
    return output_df
