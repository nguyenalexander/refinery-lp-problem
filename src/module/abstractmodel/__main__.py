import pyomo.environ as pyomo
import numpy as np
import pandas as pd
import itertools

class RefineryOptimizationAbstract:
    """Class used to create an optimization object, set-up the problem, solve, and output."""
    def __init__(self):
        """Initialization of data sets"""

        # create dictionary to map flow streams to originating and receiving units
        self.map_to_units = {
            'crude': {('crude_source', 'ad')},
            'srg': {('ad', 'srg_sp'), ('srg_sp', 'pg_tk'), ('srg_sp', 'rg_tk')},
            'srn': {('ad', 'srn_sp'), ('srn_sp', 'rf'), ('srn_sp', 'pg_tk'), ('srn_sp', 'rg_tk'), ('srn_sp', 'df_tk')},
            'srds': {('ad', 'srds_sp'), ('srds_sp', 'cc'), ('srds_sp', 'df_tk'), ('srds_sp', 'fo_tk')},
            'srfo': {('ad', 'srfo_sp'), ('srfo_sp', 'cc'), ('srfo_sp', 'df_tk'), ('srfo_sp', 'fo_tk')},
            'rfg': {('rf', 'rfg_sp'), ('rfg_sp', 'pg_tk'), ('rfg_sp', 'rg_tk')},
            'ccg': {('cc', 'ccg_sp'), ('ccg_sp', 'pg_tk'), ('ccg_sp', 'rg_tk')},
            'fo': {('cc', 'fo_sp'), ('fo_sp', 'df_tk'), ('fo_sp', 'fo_tk')},
            'fg': {('ad', 'fg_sink'), ('rf', 'fg_sink'), ('cc', 'fg_sink')},
            'pg_prod': {('pg_tk','pg_out')},
            'rg_prod': {('rg_tk','rg_out')},
            'df_prod': {('df_tk','df_out')},
            'fo_prod': {('fo_tk','fo_out')}
        }

        # costs for designated streams (operating costs, material cost, product costs)
        self.cost_data = {
            ('crude', 'crude_source', 'ad'): -33,
            ('fg', 'ad', 'fg_sink'): 0.01965,
            ('fg', 'rf', 'fg_sink'): 0.01965,
            ('srn', 'srn_sp', 'rf'): -2.5,
            ('srds', 'srds_sp', 'cc'): -2.2,
            ('srfo', 'srfo_sp', 'cc'): -2.2,
            ('fg', 'cc', 'fg_sink'): 0.01965,
            ('pg_prod', 'pg_tk','pg_out'): 45.36,
            ('rg_prod', 'rg_tk','rg_out'): 43.68,
            ('df_prod', 'df_tk','df_out'): 40.32,
            ('fo_prod', 'fo_tk','fo_out'): 13.14
        }

        # dictionary of each split origin and the respective split streams
        self.splitpoint_dict = {
            ('srg', 'ad', 'srg_sp'): {('srg', 'srg_sp', 'pg_tk'), ('srg', 'srg_sp', 'rg_tk')},
            ('srn', 'ad', 'srn_sp'): {('srn','srn_sp', 'rf'), ('srn','srn_sp', 'pg_tk'), ('srn','srn_sp', 'rg_tk'), ('srn','srn_sp', 'df_tk')},
            ('srds', 'ad', 'srds_sp'): {('srds','srds_sp', 'cc'), ('srds','srds_sp', 'df_tk'), ('srds','srds_sp', 'fo_tk')},
            ('srfo','ad', 'srfo_sp'): {('srfo','srfo_sp', 'cc'), ('srfo','srfo_sp', 'df_tk'), ('srfo','srfo_sp', 'fo_tk')},
            ('rfg', 'rf', 'rfg_sp'): {('rfg', 'rfg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'rg_tk')},
            ('ccg', 'cc', 'ccg_sp'): {('ccg','ccg_sp', 'pg_tk'), ('ccg','ccg_sp', 'rg_tk')},
            ('fo', 'cc', 'fo_sp'): {('fo', 'fo_sp', 'df_tk'), ('fo', 'fo_sp', 'fo_tk')}
        }

        # product demand data
        self.product_demand_data = {
            ('pg_prod', 'pg_tk', 'pg_out'): 10000,
            ('rg_prod', 'rg_tk', 'rg_out'): 10000,
            ('df_prod', 'df_tk', 'df_out'): 10000,
            ('fo_prod', 'fo_tk', 'fo_out'): 10000
        }

        # yield coefficients for each unit operation
        # Atmospheric Distillation
        self.ad_yield_coef = {
            ('fg', 'ad', 'fg_sink'): 35.42,
            ('srg', 'ad', 'srg_sp'): 0.270,
            ('srn', 'ad', 'srn_sp'): 0.237,
            ('srds', 'ad', 'srds_sp'): 0.087,
            ('srfo', 'ad', 'srfo_sp'): 0.372
        }

        # Reformer
        self.rf_yield_coef = {
            ('fg', 'rf', 'fg_sink'): 158.7,
            ('rfg', 'rf', 'rfg_sp'): 0.928
        }

        # Catalytic Cracker for SRDS Feed
        self.cc_srds_yield_coef = {
            ('fg', 'cc', 'fg_sink'): 336.9,
            ('ccg', 'cc', 'ccg_sp'): 0.619,
            ('fo', 'cc', 'fo_sp'): 0.189
        }

        # Catalytic Cracker for SRFO Feed
        self.cc_srfo_yield_coef = {
            ('fg', 'cc', 'fg_sink'): 386.4,
            ('ccg', 'cc', 'ccg_sp'): 0.688,
            ('fo', 'cc', 'fo_sp'): 0.2197
        }

        # Feed Properties for Blending
        # Octane Ratings
        self.pg_octane_data = {
            ('srg', 'srg_sp', 'pg_tk'): 78.5,
            ('rfg', 'rfg_sp', 'pg_tk'): 104,
            ('srn', 'srn_sp', 'pg_tk'): 65,
            ('ccg', 'ccg_sp', 'pg_tk'): 93.7
        }

        self.rg_octane_data = {
            ('srg', 'srg_sp', 'rg_tk'): 78.5,
            ('rfg', 'rfg_sp', 'rg_tk'): 104,
            ('srn', 'srn_sp', 'rg_tk'): 65,
            ('ccg', 'ccg_sp', 'rg_tk'): 93.7
        }

        # Vapour Pressures
        self.pg_vpress_data = {
            ('srg', 'srg_sp', 'pg_tk'): 18.4,
            ('rfg', 'rfg_sp', 'pg_tk'): 2.57,
            ('srn', 'srn_sp', 'pg_tk'): 6.54,
            ('ccg', 'ccg_sp', 'pg_tk'): 6.9
        }
        self.rg_vpress_data = {
            ('srg', 'srg_sp', 'rg_tk'): 18.4,
            ('rfg', 'rfg_sp', 'rg_tk'): 2.57,
            ('srn', 'srn_sp', 'rg_tk'): 6.54,
            ('ccg', 'ccg_sp', 'rg_tk'): 6.9
        }

        # Densities
        self.df_density_data = {
            ('srn', 'srn_sp', 'df_tk'): 272,
            ('fo', 'fo_sp', 'df_tk'): 294.4,
            ('srds', 'srds_sp', 'df_tk'): 292,
            ('srfo', 'srfo_sp', 'df_tk'): 295
        }

        self.fo_density_data = {
            ('fo', 'fo_sp', 'fo_tk'): 294.4,
            ('srds', 'srds_sp', 'fo_tk'): 292,
            ('srfo', 'srfo_sp', 'fo_tk'): 295
        }

        # Sulfur Concentrations
        self.df_sulfur_data = {
            ('srn', 'srn_sp', 'df_tk'): 0.283,
            ('fo', 'fo_sp', 'df_tk'): 0.353,
            ('srds', 'srds_sp', 'df_tk'): 0.526,
            ('srfo', 'srfo_sp', 'df_tk'): 0.980
        }
        self.fo_sulfur_data = {
            ('fo', 'fo_sp', 'fo_tk'): 0.353,
            ('srds', 'srds_sp', 'fo_tk'): 0.526,
            ('srfo', 'srfo_sp', 'fo_tk'): 0.980
        }

    def build_model(self):
        """
        Build the optimization model with constraints and objectives.
        Returns the Pyomo model object for solving.
        """

        # ===============================================================================
        # ================================ PROBLEM SETUP ================================
        # ===============================================================================

        # Create abstract model
        model = pyomo.AbstractModel()

        # Define main sets
        # streams = material streams
        model.materials = pyomo.Set()

        # unitpairs = combinations of units where the streams are leaving and entering
        model.unitpairs = pyomo.Set()

        # combination of the materials to the unit pairs using the map dictionary
        # initialize statement creates a list of triplet sets of the key to the value pairs (e.g. [('srg', 'ad', 'pg'), ('srg', 'ad', 'rg'), ...])
        model.flowpairs = pyomo.Set(within=model.materials * model.unitpairs, initialize = [(m, u) for m in self.map_to_units for u in self.map_to_units[m]])

        # Set of flows going into the splitpoint nodes
        model.sp_in = pyomo.Set(dimen=3)

        # Splitpoints Set (each key in dictionary is the input to the sp, and the corresponding list is the outputs)
        # Must declare the Set as the inputs and initialize with the full dictionary and added to the data dictionary as well to avoid unordered errors
        model.splitpoints = pyomo.Set(model.sp_in, initialize=self.splitpoint_dict)

        # Set for the cost streams
        model.cost_set = pyomo.Set(within=model.flowpairs, initialize=list(self.cost_data.keys()))

        # Flow rate variable
        model.x = pyomo.Var(model.flowpairs, domain=pyomo.NonNegativeReals)

        # data to fill the materials and unitpairs sets
        # unitpairs is a set of tuples for each specified combination (e.g. {('ad', 'pg'), ('ad', 'cc'), ...})
        data = { None: {
            'materials': {None: ['crude','srg','srn','srds','srfo','rfg','ccg','fo','fg','pg_prod','rg_prod','df_prod','fo_prod']},
            'unitpairs': {None: set(itertools.chain.from_iterable(self.map_to_units.values()))},
            'splitpoints': {
                ('srg', 'ad', 'srg_sp'): [('srg', 'srg_sp', 'pg_tk'), ('srg', 'srg_sp', 'rg_tk')],
                ('srn', 'ad', 'srn_sp'): [('srn', 'srn_sp', 'rf'), ('srn', 'srn_sp', 'pg_tk'), ('srn', 'srn_sp', 'rg_tk'), ('srn', 'srn_sp', 'df_tk')],
                ('srds', 'ad', 'srds_sp'): [('srds', 'srds_sp', 'cc'), ('srds', 'srds_sp', 'df_tk'), ('srds', 'srds_sp', 'fo_tk')],
                ('srfo', 'ad', 'srfo_sp'): [('srfo', 'srfo_sp', 'cc'), ('srfo', 'srfo_sp', 'df_tk'), ('srfo', 'srfo_sp', 'fo_tk')],
                ('rfg', 'rf', 'rfg_sp'): [('rfg', 'rfg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'rg_tk')],
                ('ccg', 'cc', 'ccg_sp'): [('ccg', 'ccg_sp', 'pg_tk'), ('ccg', 'ccg_sp', 'rg_tk')],
                ('fo', 'cc', 'fo_sp'): [('fo', 'fo_sp', 'df_tk'), ('fo', 'fo_sp', 'fo_tk')],
            },
            'sp_in': {None: [('srg', 'ad', 'srg_sp'), ('srn', 'ad', 'srn_sp'), ('srds', 'ad', 'srds_sp'), ('srfo', 'ad', 'srfo_sp'), ('rfg', 'rf', 'rfg_sp'), ('ccg', 'cc', 'ccg_sp'), ('fo', 'cc', 'fo_sp')]}
        }}

        # Parameter for cost streams
        model.costs = pyomo.Param(model.cost_set, initialize=self.cost_data)

        # Yields
        # Sets
        model.ad_outflows = pyomo.Set(within=model.flowpairs, initialize = [('fg', 'ad', 'fg_sink'), ('srg', 'ad', 'srg_sp'), ('srn', 'ad', 'srn_sp'), ('srds', 'ad', 'srds_sp'), ('srfo', 'ad', 'srfo_sp')])
        model.rf_outflows = pyomo.Set(within=model.flowpairs, initialize = [('fg', 'rf', 'fg_sink'), ('rfg', 'rf', 'rfg_sp')])
        model.cc_outflows = pyomo.Set(within=model.flowpairs, initialize = [('fg', 'cc', 'fg_sink'), ('ccg', 'cc', 'ccg_sp'), ('fo', 'cc', 'fo_sp')])

        # Parameters
        model.ad_yield_coef = pyomo.Param(model.ad_outflows, initialize=self.ad_yield_coef)
        model.rf_yield_coef = pyomo.Param(model.rf_outflows, initialize=self.rf_yield_coef)
        model.cc_srds_yield_coef = pyomo.Param(model.cc_outflows, initialize=self.cc_srds_yield_coef)
        model.cc_srfo_yield_coef = pyomo.Param(model.cc_outflows, initialize=self.cc_srfo_yield_coef)

        # Demand
        model.product_set = pyomo.Set(within=model.flowpairs, initialize=[('pg_prod', 'pg_tk', 'pg_out'),('rg_prod', 'rg_tk', 'rg_out'),('df_prod', 'df_tk', 'df_out'),('fo_prod', 'fo_tk', 'fo_out')])
        model.product_demand_numbers = pyomo.Param(model.product_set, initialize=self.product_demand_data)

        # Blend Tank Balance Sets
        model.pg_set = pyomo.Set(within=model.flowpairs, initialize=[('srg', 'srg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'pg_tk'), ('srn', 'srn_sp', 'pg_tk'), ('ccg', 'ccg_sp', 'pg_tk')])
        model.rg_set = pyomo.Set(within=model.flowpairs, initialize=[('srg', 'srg_sp', 'rg_tk'), ('rfg', 'rfg_sp', 'rg_tk'), ('srn', 'srn_sp', 'rg_tk'), ('ccg', 'ccg_sp', 'rg_tk')])
        model.df_set = pyomo.Set(within=model.flowpairs, initialize=[('srn', 'srn_sp', 'df_tk'), ('fo', 'fo_sp', 'df_tk'), ('srds', 'srds_sp', 'df_tk'), ('srfo', 'srfo_sp', 'df_tk')])
        model.fo_set = pyomo.Set(within=model.flowpairs, initialize=[('fo', 'fo_sp', 'fo_tk'), ('srds', 'srds_sp', 'fo_tk'), ('srfo', 'srfo_sp', 'fo_tk')])

        # Quality Constraint Parameters
        model.pg_octane_rating = pyomo.Param(model.pg_set, initialize=self.pg_octane_data)
        model.pg_vpress_rating = pyomo.Param(model.pg_set, initialize=self.pg_vpress_data)
        model.rg_octane_rating = pyomo.Param(model.rg_set, initialize=self.rg_octane_data)
        model.rg_vpress_rating = pyomo.Param(model.rg_set, initialize=self.rg_vpress_data)
        model.df_density_spec = pyomo.Param(model.df_set, initialize=self.df_density_data)
        model.df_sulfur_spec = pyomo.Param(model.df_set, initialize=self.df_sulfur_data)
        model.fo_density_spec = pyomo.Param(model.fo_set, initialize=self.fo_density_data)
        model.fo_sulfur_spec = pyomo.Param(model.fo_set, initialize=self.fo_sulfur_data)

        # ==============================================================================
        # ================================= OBJECTIVES =================================
        # ==============================================================================

        # Objective Function (profit = products - operating cost - crude cost)
        def profit_objective(model):
            return sum(model.x[c] * model.costs[c] for c in model.costs)
        model.objectivefunction = pyomo.Objective(rule=profit_objective, sense=pyomo.maximize)

        # ===============================================================================
        # ================================= CONSTRAINTS =================================
        # ===============================================================================

        # Splitpoint Balances
        def splitpoint_balance(model, mat, uin, uout):
            return model.x[mat, uin, uout] - sum(model.x[i] for i in model.splitpoints[mat, uin, uout]) == 0
        model.splitpoint_volbalance = pyomo.Constraint(model.sp_in, rule=splitpoint_balance)

        # Capacity Equations
        def ad_crude_limit(model):
            return model.x['crude', 'crude_source', 'ad'] <= 110000
        def ad_capacity(model):
            return model.x['crude', 'crude_source', 'ad'] <= 100000
        def rf_capacity(model):
            return model.x['srn', 'srn_sp', 'rf'] <= 25000
        def cc_capacity(model):
            return model.x['srds', 'srds_sp', 'cc'] + model.x['srfo', 'srfo_sp', 'cc'] <= 30000

        # Capacity Constraints
        model.crudecap = pyomo.Constraint(rule=ad_crude_limit)
        model.adcap = pyomo.Constraint(rule = ad_capacity)
        model.rfcap = pyomo.Constraint(rule = rf_capacity)
        model.cccap = pyomo.Constraint(rule = cc_capacity)

        # Yield Equations
        def ad_yield(model, mat, uin, uout):
            return model.x[mat, uin, uout] == model.x['crude', 'crude_source', 'ad'] * model.ad_yield_coef[mat, uin, uout]
        def rf_yield(model, mat, uin, uout):
            return model.x[mat, uin, uout] == model.x['srn','srn_sp','rf'] * model.rf_yield_coef[mat, uin, uout]
        def cc_yield(model, mat, uin, uout):
            return model.x[mat, uin, uout] == model.x['srds','srds_sp','cc'] * model.cc_srds_yield_coef[mat, uin, uout] + model.x['srfo','srfo_sp','cc'] * model.cc_srfo_yield_coef[mat, uin, uout]

        # Yield Constraints
        model.ad_output = pyomo.Constraint(model.ad_outflows, rule = ad_yield)
        model.rf_output = pyomo.Constraint(model.rf_outflows, rule = rf_yield)
        model.cc_output = pyomo.Constraint(model.cc_outflows, rule = cc_yield)

        # Demand Equations and Constraints
        def product_demand(model, mat, uin, uout):
            return model.x[mat, uin, uout] >= model.product_demand_numbers[mat, uin, uout]
        model.product_demand = pyomo.Constraint(model.product_set, rule = product_demand)

        # Blend Tank Balance Equations
        def pg_balance(model):
            return model.x['pg_prod', 'pg_tk', 'pg_out'] == sum(model.x[mat, uin, uout] for (mat, uin, uout) in model.pg_set)
        def rg_balance(model):
            return model.x['rg_prod', 'rg_tk', 'rg_out'] == sum(model.x[mat, uin, uout] for (mat, uin, uout) in model.rg_set)
        def df_balance(model):
            return model.x['df_prod', 'df_tk', 'df_out'] == sum(model.x[mat, uin, uout] for (mat, uin, uout) in model.df_set)
        def fo_balance(model):
            return model.x['fo_prod', 'fo_tk', 'fo_out'] == sum(model.x[mat, uin, uout] for (mat, uin, uout) in model.fo_set)

        # Blend Tank Balance Constraints
        model.pg_blend = pyomo.Constraint(rule=pg_balance)
        model.rg_blend = pyomo.Constraint(rule=rg_balance)
        model.df_blend = pyomo.Constraint(rule=df_balance)
        model.fo_blend = pyomo.Constraint(rule = fo_balance)

        # Product Quality Equations
        def pg_octane(model):
            return sum(model.x[mat, uin, uout] * model.pg_octane_rating[mat, uin, uout] for (mat, uin, uout) in model.pg_set) - 93 * model.x['pg_prod', 'pg_tk', 'pg_out'] >= 0
        def pg_vpress(model):
            return sum(model.x[mat, uin, uout] * model.pg_vpress_rating[mat, uin, uout] for (mat, uin, uout) in model.pg_set) - 12.7 * model.x['pg_prod', 'pg_tk', 'pg_out'] <= 0
        def rg_octane(model):
            return sum(model.x[mat, uin, uout] * model.rg_octane_rating[mat, uin, uout] for (mat, uin, uout) in model.rg_set) - 83 * model.x['rg_prod', 'rg_tk', 'rg_out'] >= 0
        def rg_vpress(model):
            return sum(model.x[mat, uin, uout] * model.rg_vpress_rating[mat, uin, uout] for (mat, uin, uout) in model.rg_set) - 12.7 * model.x['rg_prod', 'rg_tk', 'rg_out'] <= 0
        def df_density(model):
            return sum(model.x[mat, uin, uout] * model.df_density_spec[mat, uin, uout] for (mat, uin, uout) in model.df_set) - 306 * model.x['df_prod', 'df_tk', 'df_out'] <= 0
        def df_sulfur(model):
            return sum(model.x[mat, uin, uout] * model.df_sulfur_spec[mat, uin, uout] for (mat, uin, uout) in model.df_set) - 0.50 * model.x['df_prod', 'df_tk', 'df_out'] <= 0
        def fo_density(model):
            return sum(model.x[mat, uin, uout] * model.fo_density_spec[mat, uin, uout] for (mat, uin, uout) in model.fo_set) - 352 * model.x['fo_prod', 'fo_tk', 'fo_out'] <= 0
        def fo_sulfur(model):
            return sum(model.x[mat, uin, uout] * model.fo_sulfur_spec[mat, uin, uout] for (mat, uin, uout) in model.fo_set) - 3.0 * model.x['fo_prod', 'fo_tk', 'fo_out'] <= 0

        # Product Quality Constraints
        model.pg_octane_req = pyomo.Constraint(rule=pg_octane)
        model.pg_vpress_req = pyomo.Constraint(rule=pg_vpress)
        model.rg_octane_req = pyomo.Constraint(rule=rg_octane)
        model.rg_vpress_req = pyomo.Constraint(rule=rg_vpress)
        model.df_density_req = pyomo.Constraint(rule=df_density)
        model.df_sulfur_req = pyomo.Constraint(rule=df_sulfur)
        model.fo_density_req = pyomo.Constraint(rule=fo_density)
        model.fo_sulfur_req = pyomo.Constraint(rule=fo_sulfur)

        # Create instance of model
        instance = model.create_instance(data)

        # Fix if required
        # instance.x['crude', 'crude_source', 'ad'].fix(100000)

        # Display instance information
        instance.pprint()

        return instance

    def execute_optimization(self):
        """Builds the Pyomo Model then solves the optimization problem. Returns the solved model object."""
        opt_model = self.build_model()
        solver = pyomo.SolverFactory('glpk')
        solver.solve(opt_model, tee=True)

        return opt_model

    def print_output(self, opt_model):
        """Prints the flow rates, then the total profit and production of each product and their properties."""
        opt_model.display()

def main():
    # initialize refinery class
    refinery_problem = RefineryOptimizationAbstract()

    # solve optimization problem
    optimization_result = refinery_problem.execute_optimization()

    # print results using results
    refinery_problem.print_output(optimization_result)


if __name__ == "__main__":
    main()