import pyomo.environ as pyomo
from src.refinery_problem import helpers
import pandas as pd


def execute_optimization(opt_model):
    """Case study #2: only CCG buffer tank after the catalytic cracker."""

    for t in range(1, opt_model.timeperiods.ordered_data()[-1] + 1, opt_model.timeperiods.ordered_data()[-1] - opt_model.timeperiods.ordered_data()[-2]):
        # SRN tank off
        opt_model.x['srn', 'srn_sp', 'srn_tk', t].fix(0)

        # RFG tank off
        opt_model.x['rfg', 'rf', 'rfg_tk', t].fix(0)

        # CCG tank off
        # opt_model.x['ccg', 'cc', 'ccg_tk', t].fix(0)

        # CCFO tank off
        opt_model.x['ccfo', 'cc', 'ccfo_tk', t].fix(0)

    # Shutdown scenarios
    shutdown_conditions = {
        1: [('cc', 3)],
        2: [('cc', 2), ('cc', 3)],
        3: [('rf', 3)],
        4: [('rf', 2), ('rf', 3)],
        5: [('rf', 3), ('cc', 1)],
        6: [('rf', 3), ('cc', 2)],
        7: [('rf', 3), ('cc', 3)],
        8: [('rf', 1), ('cc', 4)],
        9: [('rf', 2), ('cc', 4)],
        10: [('rf', 3), ('cc', 4)]
    }

    output_results_df = pd.DataFrame()
    # Run all shutdown scenarios and store results in a dataframe column
    for case, alpha_list in shutdown_conditions.items():
        # SET Alphas for shutdown scenario
        for sd_pair in alpha_list:
            opt_model.alpha[sd_pair[0], sd_pair[1]] = 1

        # Display instance information
        # opt_model.pprint()

        # Solve optimization problem
        solver = pyomo.SolverFactory('glpk')
        solver_information = solver.solve(opt_model, tee=True)

        # Display model results
        # opt_model.display()

        # Format results into a sorted pandas series and then append to the results dataframe
        results_series = helpers.store_results_pd(opt_model, solver_information)
        output_results_df[case] = results_series

        # RESET Alpha
        for sd_pair in alpha_list:
            opt_model.alpha[sd_pair[0], sd_pair[1]] = 0

    return opt_model, output_results_df
