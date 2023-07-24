import pyomo.environ as pyomo


def execute_optimization(opt_model):
    """Case study #5: CCFO and RFG buffer tanks."""

    for t in range(1, opt_model.timeperiods.ordered_data()[-1] + 1, opt_model.timeperiods.ordered_data()[-1] - opt_model.timeperiods.ordered_data()[-2]):
        # SRN tank off
        opt_model.x['srn', 'srn_sp', 'srn_tk', t].fix(0)

        # RFG tank off
        # opt_model.x['rfg', 'rf', 'rfg_tk', t].fix(0)

        # CCG tank off
        opt_model.x['ccg', 'cc', 'ccg_tk', t].fix(0)

        # CCFO tank off
        # opt_model.x['ccfo', 'cc', 'ccfo_tk', t].fix(0)

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

    for case, alpha_list in shutdown_conditions.items():
        for sd_pair in alpha_list:
            opt_model.alpha[sd_pair[0], sd_pair[1]] = 1

        # Display instance information
        opt_model.pprint()

        solver = pyomo.SolverFactory('glpk')
        solver.solve(opt_model, tee=True)

        # opt_model.display()

        # Display Alpha for verification purposes
        # for t in range(1, opt_model.timeperiods.ordered_data()[-1] + 1, opt_model.timeperiods.ordered_data()[-1] - opt_model.timeperiods.ordered_data()[-2]):
        #     print('rf_alpha, t=', t, ': ', pyomo.value(opt_model.alpha['rf', t]))
        #     print('cc_alpha, t=', t, ': ', pyomo.value(opt_model.alpha['cc', t]))

        # RESET Alpha
        for sd_pair in alpha_list:
            opt_model.alpha[sd_pair[0], sd_pair[1]] = 0

    return opt_model