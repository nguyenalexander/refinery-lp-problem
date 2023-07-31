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
        if solver_information.solver.termination_condition == 'optimal':
            store_values.append(pyomo.value(v))
        else:
            store_values.append(0)

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

    # Add objective value to top and termination conditions
    if solver_information.solver.termination_condition == 'optimal':
        for obj in opt_model.component_data_objects(pyomo.Objective):
            store_index.insert(0, 'Objective')
            store_values.insert(0, pyomo.value(obj))
        store_index.insert(0, 'Termination Condition')
        store_values.insert(0, solver_information.solver.termination_condition)
        store_index.insert(0, 'Solver Status')
        store_values.insert(0, solver_information.solver.status)
    else:
        store_index.insert(0, 'Objective')
        store_values.insert(0, 0)
        store_index.insert(0, 'Termination Condition')
        store_values.insert(0, 'infeasible')
        store_index.insert(0, 'Solver Status')
        store_values.insert(0, 'failed')

    output_df = pd.Series(data=store_values, index=store_index)
    return output_df


def plot_charts(results_df, case_number):
    # create figure and subplots
    fig = plt.figure(figsize=(16, 6), layout='constrained')
    gs = fig.add_gridspec(4, 10, hspace=0.05, wspace=0.1)
    axs = gs.subplots(sharex=True, sharey=False)

    # for each tank, create the chart for each scenario
    tank_list = ['rfg_tk', 'ccfo_tk', 'ccg_tk', 'srn_tk']
    for tank_idx, tank_name in enumerate(tank_list):
        for scenario_idx in range(0, results_df.shape[1], 1):
            scenario_col_name = results_df.columns[scenario_idx]
            # helper function create_chart
            create_chart(axs[tank_idx, scenario_idx], results_df, tank_name, scenario_col_name, {'marker': 'o'})

    # give each column and row a label/title
    rows = ['{} Tank'.format(col) for col in ['RFG', 'CCFO', 'CCG', 'SRN']]
    cols = ['Scenario {0}\n({1})'.format(row, results_df.loc['Termination Condition', row]) for row in range(1, results_df.shape[1]+1, 1)]

    # column titles
    for ax, col in zip(axs[0], cols):
        ax.set_title(col)

    # Order: 'RFG', 'CCFO', 'CCG', 'SRN'
    tank_max = {0: 19000,
                1: 19000,
                2: 25000,
                3: 19000}
    row_ticks = {0: [0, 6000, 12000, 18000],
                 1: [0, 6000, 12000, 18000],
                 2: [0, 8000, 16000, 24000],
                 3: [0, 6000, 12000, 18000]}

    # set y limits and ticks for each row (tank)
    for i, j in enumerate(axs):
        for k in j:
            k.set_ylim(bottom=0, top=tank_max[i])
            k.set_yticks(row_ticks[i])

    # row labels
    for ax, row in zip(axs[:, 0], rows):
        ax.set_ylabel(row, rotation=0, size='medium', loc='center', labelpad=30)

    # set axis limits and ticks and bottom x labels
    # plt.setp(axs, ylim=[0, 18000], yticks=[0, 5000,  10000, 15000], xlim=[1, 5], xticks=[1, 2, 3, 4, 5], xlabel='Period (d)')
    plt.setp(axs, xlim=[1, 5], xticks=[1, 2, 3, 4, 5], xlabel='Period (d)')

    # only show the outer labels
    for ax in axs.flat:
        ax.label_outer()

    # plot title and size
    fig.suptitle('Tank Inventories (m3) for Case Study {}'.format(case_number))
    fig.get_layout_engine().set(rect=(0, 0, 1, 1))

    fig.savefig('./results/case_study_0{}.png'.format(case_number))
    # fig.show()



def create_chart(ax, results_df, tank, scenario, param_dict):
    """
    A helper function to make the results graph.
    """

    y = []
    for t in range(1, 6, 1):
        tank_str = 'm[' + tank + ',' + str(t) + ']'
        y.append(results_df.loc[tank_str, scenario])

    plots_out = ax.plot(range(1, 6, 1), y, **param_dict)
    return plots_out
