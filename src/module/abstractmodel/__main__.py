import pyomo.environ as pyomo
import numpy as np
import pandas as pd
import itertools
from collections import defaultdict


class RefineryOptimizationAbstract:
    """Class used to create an optimization object, set-up the problem, solve, and output."""

    def __init__(self):
        """
        Initialization of sets and data for the multiperiod problem
        Note: to add a new buffer tank, the user must modify:
        A: self.map_to_units
        B: self.cost_data
        C: self.splitpoint_dict
        D: Tank data in init
        E: Yield equations in self.build_model
        """

        self.timehorizon = 5
        self.timedelta = 1

        # shutdown parameter - 1 for shutdown, 0 elsewhere
        self.alpha_param = {
            'ad': 0,
            'rf': 0,
            'cc': 0
        }

        # create dictionary to map flow streams to originating and receiving units
        self.map_to_units = {
            'crude': {('crude_source', 'ad')},
            'srg': {('ad', 'srg_sp'), ('srg_sp', 'pg_tk'), ('srg_sp', 'rg_tk')},
            'srn': {('ad', 'srn_sp'), ('srn_sp', 'rf'), ('srn_sp', 'pg_tk'), ('srn_sp', 'rg_tk'), ('srn_sp', 'df_tk'), ('srn_sp', 'srn_tk'), ('srn_tk', 'rf')},  # NEW
            'srds': {('ad', 'srds_sp'), ('srds_sp', 'cc'), ('srds_sp', 'df_tk'), ('srds_sp', 'fo_tk')},
            'srfo': {('ad', 'srfo_sp'), ('srfo_sp', 'cc'), ('srfo_sp', 'df_tk'), ('srfo_sp', 'fo_tk')},
            'rfg': {('rf', 'rfg_sp'), ('rfg_sp', 'pg_tk'), ('rfg_sp', 'rg_tk'), ('rf', 'rfg_tk'), ('rfg_tk', 'rfg_sp')},  # NEW
            'ccg': {('cc', 'ccg_sp'), ('ccg_sp', 'pg_tk'), ('ccg_sp', 'rg_tk'), ('cc', 'ccg_tk'), ('ccg_tk', 'ccg_sp')},  # NEW
            'ccfo': {('cc', 'ccfo_sp'), ('ccfo_sp', 'df_tk'), ('ccfo_sp', 'fo_tk'), ('cc', 'ccfo_tk'), ('ccfo_tk', 'ccfo_sp')},  # NEW
            'fg': {('ad', 'fg_sink'), ('rf', 'fg_sink'), ('cc', 'fg_sink')},
            'pg_prod': {('pg_tk', 'pg_out')},
            'rg_prod': {('rg_tk', 'rg_out')},
            'df_prod': {('df_tk', 'df_out')},
            'fo_prod': {('fo_tk', 'fo_out')}
        }

        # costs for designated streams (operating costs, material cost, product costs)
        self.cost_data = {
            ('crude', 'crude_source', 'ad'): -33,
            ('fg', 'ad', 'fg_sink'): 0.01965,
            ('fg', 'rf', 'fg_sink'): 0.01965,
            ('srn', 'srn_sp', 'rf'): -2.5,
            ('srn', 'srn_tk', 'rf'): -2.5,  # NEW
            ('srds', 'srds_sp', 'cc'): -2.2,
            ('srfo', 'srfo_sp', 'cc'): -2.2,
            ('fg', 'cc', 'fg_sink'): 0.01965,
            ('pg_prod', 'pg_tk', 'pg_out'): 45.36,
            ('rg_prod', 'rg_tk', 'rg_out'): 43.68,
            ('df_prod', 'df_tk', 'df_out'): 40.32,
            ('fo_prod', 'fo_tk', 'fo_out'): 13.14,
            ('srn', 'srn_sp', 'srn_tk'): -0.5,  # NEW
            ('rfg', 'rf', 'rfg_tk'): -0.5,  # NEW
            ('ccg', 'cc', 'ccg_tk'): -0.5,  # NEW
            ('ccfo', 'cc', 'ccfo_tk'): -0.5  # NEW
        }

        # dictionary of each split origin (key) and the respective split streams (values)
        self.splitpoint_dict = {
            ('srg', 'ad', 'srg_sp'): {('srg', 'srg_sp', 'pg_tk'), ('srg', 'srg_sp', 'rg_tk')},
            ('srn', 'ad', 'srn_sp'): {('srn', 'srn_sp', 'rf'), ('srn', 'srn_sp', 'pg_tk'), ('srn', 'srn_sp', 'rg_tk'), ('srn', 'srn_sp', 'df_tk'), ('srn', 'srn_sp', 'srn_tk')},
            ('srds', 'ad', 'srds_sp'): {('srds', 'srds_sp', 'cc'), ('srds', 'srds_sp', 'df_tk'), ('srds', 'srds_sp', 'fo_tk')},
            ('srfo', 'ad', 'srfo_sp'): {('srfo', 'srfo_sp', 'cc'), ('srfo', 'srfo_sp', 'df_tk'), ('srfo', 'srfo_sp', 'fo_tk')},
            ('rfg', 'rf', 'rfg_sp'): {('rfg', 'rfg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'rg_tk')},
            ('rfg', 'rfg_tk', 'rfg_sp'): {('rfg', 'rfg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'rg_tk')},  # NEW
            ('ccg', 'cc', 'ccg_sp'): {('ccg', 'ccg_sp', 'pg_tk'), ('ccg', 'ccg_sp', 'rg_tk')},
            ('ccg', 'ccg_tk', 'ccg_sp'): {('ccg', 'ccg_sp', 'pg_tk'), ('ccg', 'ccg_sp', 'rg_tk')},  # NEW
            ('ccfo', 'cc', 'ccfo_sp'): {('ccfo', 'ccfo_sp', 'df_tk'), ('ccfo', 'ccfo_sp', 'fo_tk')},
            ('ccfo', 'ccfo_tk', 'ccfo_sp'): {('ccfo', 'ccfo_sp', 'df_tk'), ('ccfo', 'ccfo_sp', 'fo_tk')}  # NEW
        }

        # assign the timeperiods to the splitpoints
        self.splitpoint_dict_mp = {}
        for t in range(1, self.timehorizon+1, 1):
            for i in self.splitpoint_dict:
                self.splitpoint_dict_mp[(i + (t,))] = {(j + (t,)) for j in self.splitpoint_dict[i]}

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
            ('ccfo', 'cc', 'ccfo_sp'): 0.189
        }

        # Catalytic Cracker for SRFO Feed
        self.cc_srfo_yield_coef = {
            ('fg', 'cc', 'fg_sink'): 386.4,
            ('ccg', 'cc', 'ccg_sp'): 0.688,
            ('ccfo', 'cc', 'ccfo_sp'): 0.2197
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
            ('ccfo', 'ccfo_sp', 'df_tk'): 294.4,
            ('srds', 'srds_sp', 'df_tk'): 292,
            ('srfo', 'srfo_sp', 'df_tk'): 295
        }
        self.fo_density_data = {
            ('ccfo', 'ccfo_sp', 'fo_tk'): 294.4,
            ('srds', 'srds_sp', 'fo_tk'): 292,
            ('srfo', 'srfo_sp', 'fo_tk'): 295
        }

        # Sulfur Concentrations
        self.df_sulfur_data = {
            ('srn', 'srn_sp', 'df_tk'): 0.283,
            ('ccfo', 'ccfo_sp', 'df_tk'): 0.353,
            ('srds', 'srds_sp', 'df_tk'): 0.526,
            ('srfo', 'srfo_sp', 'df_tk'): 0.980
        }
        self.fo_sulfur_data = {
            ('ccfo', 'ccfo_sp', 'fo_tk'): 0.353,
            ('srds', 'srds_sp', 'fo_tk'): 0.526,
            ('srfo', 'srfo_sp', 'fo_tk'): 0.980
        }

        # Tank data
        self.tank_height = {
            'srn_tk': 10,
            'rfg_tk': 10,
            'ccg_tk': 10,
            'ccfo_tk': 10
        }
        self.tank_radius = {
            'srn_tk': 5,
            'rfg_tk': 5,
            'ccg_tk': 5,
            'ccfo_tk': 5
        }
        self.tank_area = {
            'srn_tk': (2*np.pi*self.tank_radius['srn_tk'] * self.tank_height['srn_tk'] + np.pi*self.tank_radius['srn_tk']**2),  # m2
            'rfg_tk': (2*np.pi*self.tank_radius['rfg_tk'] * self.tank_height['rfg_tk'] + np.pi*self.tank_radius['rfg_tk']**2),  # m2
            'ccg_tk': (2*np.pi*self.tank_radius['ccg_tk'] * self.tank_height['ccg_tk'] + np.pi*self.tank_radius['ccg_tk']**2),  # m2
            'ccfo_tk': (2*np.pi*self.tank_radius['ccfo_tk'] * self.tank_height['ccfo_tk'] + np.pi*self.tank_radius['ccfo_tk']**2)  # m2
        }
        self.bbl_to_m3 = 0.158  # 0.158m3/bbl
        self.tank_list = ['srn_tk', 'rfg_tk', 'ccg_tk', 'ccfo_tk']
        self.tank_in_dict = {
            'srn_tk': [('srn', 'srn_sp', 'srn_tk')],
            'rfg_tk': [('rfg', 'rf', 'rfg_tk')],
            'ccg_tk': [('ccg', 'cc', 'ccg_tk')],
            'ccfo_tk': [('ccfo', 'cc', 'ccfo_tk')]
        }
        self.tank_out_dict = {
            'srn_tk': [('srn', 'srn_tk', 'rf')],
            'rfg_tk': [('rfg', 'rfg_tk', 'rfg_sp')],
            'ccg_tk': [('ccg', 'ccg_tk', 'ccg_sp')],
            'ccfo_tk': [('ccfo', 'ccfo_tk', 'ccfo_sp')]
        }
        self.tank_holding_cost_data = {
            'srn_tk': 1.5,
            'rfg_tk': 1.5,
            'ccg_tk': 1.5,
            'ccfo_tk': 1.5
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

        # time periods
        model.timeperiods = pyomo.Set(initialize=pyomo.RangeSet(1, self.timehorizon, 1))

        # unitpairs = combinations of units where the streams are leaving and entering
        model.unitpairs = pyomo.Set()

        # combination of the materials to the unit pairs using the map dictionary
        # initialize statement creates a list of triplet sets of the key to the value pairs (e.g. [('srg', 'ad', 'pg'), ('srg', 'ad', 'rg'), ...])
        model.flowpairs = pyomo.Set(within=model.materials * model.unitpairs * model.timeperiods, initialize=[(m, u, t) for m in self.map_to_units for u in self.map_to_units[m] for t in pyomo.RangeSet(1, self.timehorizon, 1)])

        # Elements used to create the splitpoints set
        # sp_materials = material going into splitpoint
        # sp_uout = unit that material is leaving from
        # sp_uin = splitpoint node that the material is entering
        model.sp_materials = pyomo.Set(initialize=(i for (i, j, k, t) in self.splitpoint_dict_mp))
        model.sp_uout = pyomo.Set(initialize=(j for (i, j, k, t) in self.splitpoint_dict_mp))
        model.sp_uin = pyomo.Set(initialize=(k for (i, j, k, t) in self.splitpoint_dict_mp))

        # Splitpoints Set - set as the splitpoint_dict_mp keys
        model.splitpoint_set = pyomo.Set(within=model.sp_materials * model.sp_uout * model.sp_uin * model.timeperiods, initialize=list(self.splitpoint_dict_mp.keys()))
        # model.e1 = pyomo.Set(model.d1, initialize=self.splitpoint_dict_mp1)

        # Set for the cost streams
        model.cost_set = pyomo.Set(initialize=list(self.cost_data.keys()))

        # Flow rate variable
        model.x = pyomo.Var(model.flowpairs, domain=pyomo.NonNegativeReals)

        # data to fill the materials and unitpairs sets
        # unitpairs is a set of tuples for each specified combination (e.g. {('ad', 'pg'), ('ad', 'cc'), ...})
        data = {None: {
            'materials': {None: ['crude', 'srg', 'srn', 'srds', 'srfo', 'rfg', 'ccg', 'ccfo', 'fg', 'pg_prod', 'rg_prod', 'df_prod', 'fo_prod']},
            'unitpairs': {None: set(itertools.chain.from_iterable(self.map_to_units.values()))}
        }}

        # Parameter for shutdown binary alpha
        model.alpha = pyomo.Param(self.alpha_param.keys(), initialize=self.alpha_param)

        # Parameter for cost streams
        model.costs = pyomo.Param(model.cost_set, initialize=self.cost_data)

        # Yields
        # Sets
        model.ad_outflows = pyomo.Set(initialize=[('fg', 'ad', 'fg_sink'), ('srg', 'ad', 'srg_sp'), ('srn', 'ad', 'srn_sp'), ('srds', 'ad', 'srds_sp'), ('srfo', 'ad', 'srfo_sp')])
        model.rf_outflows = pyomo.Set(initialize=[('fg', 'rf', 'fg_sink'), ('rfg', 'rf', 'rfg_sp')])
        model.cc_outflows = pyomo.Set(initialize=[('fg', 'cc', 'fg_sink'), ('ccg', 'cc', 'ccg_sp'), ('ccfo', 'cc', 'ccfo_sp')])

        # Parameters
        model.ad_yield_coef = pyomo.Param(model.ad_outflows, initialize=self.ad_yield_coef)
        model.rf_yield_coef = pyomo.Param(model.rf_outflows, initialize=self.rf_yield_coef)
        model.cc_srds_yield_coef = pyomo.Param(model.cc_outflows, initialize=self.cc_srds_yield_coef)
        model.cc_srfo_yield_coef = pyomo.Param(model.cc_outflows, initialize=self.cc_srfo_yield_coef)

        # Demand
        model.product_set = pyomo.Set(initialize=[('pg_prod', 'pg_tk', 'pg_out'), ('rg_prod', 'rg_tk', 'rg_out'), ('df_prod', 'df_tk', 'df_out'), ('fo_prod', 'fo_tk', 'fo_out')])
        model.product_demand_numbers = pyomo.Param(model.product_set, initialize=self.product_demand_data)

        # Blend Tank Balance Sets
        model.pg_set = pyomo.Set(initialize=[('srg', 'srg_sp', 'pg_tk'), ('rfg', 'rfg_sp', 'pg_tk'), ('srn', 'srn_sp', 'pg_tk'), ('ccg', 'ccg_sp', 'pg_tk')])
        model.rg_set = pyomo.Set(initialize=[('srg', 'srg_sp', 'rg_tk'), ('rfg', 'rfg_sp', 'rg_tk'), ('srn', 'srn_sp', 'rg_tk'), ('ccg', 'ccg_sp', 'rg_tk')])
        model.df_set = pyomo.Set(initialize=[('srn', 'srn_sp', 'df_tk'), ('ccfo', 'ccfo_sp', 'df_tk'), ('srds', 'srds_sp', 'df_tk'), ('srfo', 'srfo_sp', 'df_tk')])
        model.fo_set = pyomo.Set(initialize=[('ccfo', 'ccfo_sp', 'fo_tk'), ('srds', 'srds_sp', 'fo_tk'), ('srfo', 'srfo_sp', 'fo_tk')])

        # Quality Constraint Parameters
        model.pg_octane_rating = pyomo.Param(model.pg_set, initialize=self.pg_octane_data)
        model.pg_vpress_rating = pyomo.Param(model.pg_set, initialize=self.pg_vpress_data)
        model.rg_octane_rating = pyomo.Param(model.rg_set, initialize=self.rg_octane_data)
        model.rg_vpress_rating = pyomo.Param(model.rg_set, initialize=self.rg_vpress_data)
        model.df_density_spec = pyomo.Param(model.df_set, initialize=self.df_density_data)
        model.df_sulfur_spec = pyomo.Param(model.df_set, initialize=self.df_sulfur_data)
        model.fo_density_spec = pyomo.Param(model.fo_set, initialize=self.fo_density_data)
        model.fo_sulfur_spec = pyomo.Param(model.fo_set, initialize=self.fo_sulfur_data)

        # Tanks
        model.tank_set = pyomo.Set(initialize=self.tank_list)
        model.tank_in_set = pyomo.Set(model.tank_set, initialize=self.tank_in_dict)
        model.tank_out_set = pyomo.Set(model.tank_set, initialize=self.tank_out_dict)
        model.tank_holding_cost = pyomo.Param(self.tank_holding_cost_data.keys(), initialize=self.tank_holding_cost_data)
        model.m = pyomo.Var(model.tank_set, model.timeperiods, domain=pyomo.NonNegativeReals)

        # ==============================================================================
        # ================================= OBJECTIVES =================================
        # ==============================================================================

        # Objective Function (profit = products - operating cost - crude cost)
        def profit_objective(model):
            return sum(model.x[c, t] * model.costs[c] for c in model.costs for t in model.timeperiods) - sum(model.tank_holding_cost[tank] * model.m[tank, t] for tank in model.tank_set for t in model.timeperiods)

        model.objectivefunction = pyomo.Objective(rule=profit_objective, sense=pyomo.maximize)

        # ===============================================================================
        # ================================= CONSTRAINTS =================================
        # ===============================================================================

        # Splitpoint Balances
        def splitpoint_balance(model, mat, uout, uin, t):
            # get the outlet streams of the current originating splitpoint
            sp_outlets = self.splitpoint_dict_mp[mat, uout, uin, t]

            # loop through the sp inlet streams - if any inlet streams share the same outlet streams, then add to list
            inlet_stream_list = []
            for i in self.splitpoint_dict_mp:
                if self.splitpoint_dict_mp[i] == sp_outlets:
                    inlet_stream_list.append(i)

            # sum of flows into a splitpoint node are equal to the sum of flows out of a node
            return sum(model.x[j] for j in inlet_stream_list) - sum(model.x[a, b, c, t] for (a, b, c) in self.splitpoint_dict[mat, uout, uin]) == 0
        model.splitpoint_volbalance = pyomo.Constraint(model.splitpoint_set, rule=splitpoint_balance)

        # Capacity Equations
        def ad_crude_limit(model, t):
            return model.x['crude', 'crude_source', 'ad', t] <= 110000

        def ad_capacity(model, t):
            return model.x['crude', 'crude_source', 'ad', t] * (1 - model.alpha['ad']) <= 100000

        def rf_capacity(model, t):
            return (model.x['srn', 'srn_sp', 'rf', t] + model.x['srn', 'srn_tk', 'rf', t]) * (1 - model.alpha['rf']) <= 25000

        def cc_capacity(model, t):
            return (model.x['srds', 'srds_sp', 'cc', t] + model.x['srfo', 'srfo_sp', 'cc', t]) * (1 - model.alpha['cc']) <= 30000

        # Capacity Constraints
        model.crudecap = pyomo.Constraint(model.timeperiods, rule=ad_crude_limit)
        model.adcap = pyomo.Constraint(model.timeperiods, rule=ad_capacity)
        model.rfcap = pyomo.Constraint(model.timeperiods, rule=rf_capacity)
        model.cccap = pyomo.Constraint(model.timeperiods, rule=cc_capacity)

        # Yield Equations
        def ad_yield(model, mat, uout, uin, t):
            return model.x[mat, uout, uin, t] == model.x['crude', 'crude_source', 'ad', t] * model.ad_yield_coef[mat, uout, uin]

        def rf_yield(model, mat, uout, uin, t):
            if mat == 'rfg':
                return model.x[mat, uout, uin, t] + model.x[mat, 'rf', 'rfg_tk', t] == model.x['srn', 'srn_sp', 'rf', t] * model.rf_yield_coef[mat, uout, uin] + model.x['srn', 'srn_tk', 'rf', t] * model.rf_yield_coef[mat, uout, uin]
            else:
                return model.x[mat, uout, uin, t] == model.x['srn', 'srn_sp', 'rf', t] * model.rf_yield_coef[mat, uout, uin] + model.x['srn', 'srn_tk', 'rf', t] * model.rf_yield_coef[mat, uout, uin]

        def cc_yield(model, mat, uout, uin, t):
            if mat == 'ccg':
                return model.x[mat, uout, uin, t] + model.x[mat, 'cc', 'ccg_tk', t] == model.x['srds', 'srds_sp', 'cc', t] * model.cc_srds_yield_coef[mat, uout, uin] + model.x['srfo', 'srfo_sp', 'cc', t] * model.cc_srfo_yield_coef[mat, uout, uin]
            elif mat == 'ccfo':
                return model.x[mat, uout, uin, t] + model.x[mat, 'cc', 'ccfo_tk', t] == model.x['srds', 'srds_sp', 'cc', t] * model.cc_srds_yield_coef[mat, uout, uin] + model.x['srfo', 'srfo_sp', 'cc', t] * model.cc_srfo_yield_coef[mat, uout, uin]
            else:
                return model.x[mat, uout, uin, t] == model.x['srds', 'srds_sp', 'cc', t] * model.cc_srds_yield_coef[mat, uout, uin] + model.x['srfo', 'srfo_sp', 'cc', t] * model.cc_srfo_yield_coef[mat, uout, uin]

        # Yield Constraints
        model.ad_output = pyomo.Constraint(model.ad_outflows, model.timeperiods, rule=ad_yield)
        model.rf_output = pyomo.Constraint(model.rf_outflows, model.timeperiods, rule=rf_yield)
        model.cc_output = pyomo.Constraint(model.cc_outflows, model.timeperiods, rule=cc_yield)

        # Demand Equations and Constraints
        def product_demand(model, mat, uout, uin, t):
            return model.x[mat, uout, uin, t] >= model.product_demand_numbers[mat, uout, uin]

        model.product_demand = pyomo.Constraint(model.product_set, model.timeperiods, rule=product_demand)

        # Blend Tank Balance Equations
        def pg_balance(model, t):
            return model.x['pg_prod', 'pg_tk', 'pg_out', t] == sum(model.x[mat, uout, uin, t] for (mat, uout, uin) in model.pg_set)

        def rg_balance(model, t):
            return model.x['rg_prod', 'rg_tk', 'rg_out', t] == sum(model.x[mat, uout, uin, t] for (mat, uout, uin) in model.rg_set)

        def df_balance(model, t):
            return model.x['df_prod', 'df_tk', 'df_out', t] == sum(model.x[mat, uout, uin, t] for (mat, uout, uin) in model.df_set)

        def fo_balance(model, t):
            return model.x['fo_prod', 'fo_tk', 'fo_out', t] == sum(model.x[mat, uout, uin, t] for (mat, uout, uin) in model.fo_set)

        # Blend Tank Balance Constraints
        model.pg_blend = pyomo.Constraint(model.timeperiods, rule=pg_balance)
        model.rg_blend = pyomo.Constraint(model.timeperiods, rule=rg_balance)
        model.df_blend = pyomo.Constraint(model.timeperiods, rule=df_balance)
        model.fo_blend = pyomo.Constraint(model.timeperiods, rule=fo_balance)

        # Product Quality Equations
        def pg_octane(model, t):
            return sum(model.x[mat, uout, uin, t] * model.pg_octane_rating[mat, uout, uin] for (mat, uout, uin) in model.pg_set) - 93 * model.x['pg_prod', 'pg_tk', 'pg_out', t] >= 0

        def pg_vpress(model, t):
            return sum(model.x[mat, uout, uin, t] * model.pg_vpress_rating[mat, uout, uin] for (mat, uout, uin) in model.pg_set) - 12.7 * model.x['pg_prod', 'pg_tk', 'pg_out', t] <= 0

        def rg_octane(model, t):
            return sum(model.x[mat, uout, uin, t] * model.rg_octane_rating[mat, uout, uin] for (mat, uout, uin) in model.rg_set) - 83 * model.x['rg_prod', 'rg_tk', 'rg_out', t] >= 0

        def rg_vpress(model, t):
            return sum(model.x[mat, uout, uin, t] * model.rg_vpress_rating[mat, uout, uin] for (mat, uout, uin) in model.rg_set) - 12.7 * model.x['rg_prod', 'rg_tk', 'rg_out', t] <= 0

        def df_density(model, t):
            return sum(model.x[mat, uout, uin, t] * model.df_density_spec[mat, uout, uin] for (mat, uout, uin) in model.df_set) - 306 * model.x['df_prod', 'df_tk', 'df_out', t] <= 0

        def df_sulfur(model, t):
            return sum(model.x[mat, uout, uin, t] * model.df_sulfur_spec[mat, uout, uin] for (mat, uout, uin) in model.df_set) - 0.50 * model.x['df_prod', 'df_tk', 'df_out', t] <= 0

        def fo_density(model, t):
            return sum(model.x[mat, uout, uin, t] * model.fo_density_spec[mat, uout, uin] for (mat, uout, uin) in model.fo_set) - 352 * model.x['fo_prod', 'fo_tk', 'fo_out', t] <= 0

        def fo_sulfur(model, t):
            return sum(model.x[mat, uout, uin, t] * model.fo_sulfur_spec[mat, uout, uin] for (mat, uout, uin) in model.fo_set) - 3.0 * model.x['fo_prod', 'fo_tk', 'fo_out', t] <= 0

        # Product Quality Constraints
        model.pg_octane_req = pyomo.Constraint(model.timeperiods, rule=pg_octane)
        model.pg_vpress_req = pyomo.Constraint(model.timeperiods, rule=pg_vpress)
        model.rg_octane_req = pyomo.Constraint(model.timeperiods, rule=rg_octane)
        model.rg_vpress_req = pyomo.Constraint(model.timeperiods, rule=rg_vpress)
        model.df_density_req = pyomo.Constraint(model.timeperiods, rule=df_density)
        model.df_sulfur_req = pyomo.Constraint(model.timeperiods, rule=df_sulfur)
        model.fo_density_req = pyomo.Constraint(model.timeperiods, rule=fo_density)
        model.fo_sulfur_req = pyomo.Constraint(model.timeperiods, rule=fo_sulfur)

        # ===============================================================================
        # ==================================== TANKS ====================================
        # ===============================================================================

        def tank_balance(model, tank, t):
            if t == 1:
                return (model.m[tank, t] - 0)/self.timedelta - sum(model.x[a, b, c, t] for (a, b, c) in model.tank_in_set[tank]) + sum(model.x[d, e, f, t] for (d, e, f) in model.tank_out_set[tank]) == 0
            else:
                return (model.m[tank, t] - model.m[tank, t-1])/self.timedelta - sum(model.x[a, b, c, t] for (a, b, c) in model.tank_in_set[tank]) + sum(model.x[d, e, f, t] for (d, e, f) in model.tank_out_set[tank]) == 0
        model.tank_volbalance = pyomo.Constraint(model.tank_set, model.timeperiods, rule=tank_balance)

        def tank_height(model, tank, t):
            return model.m[tank, t] * self.bbl_to_m3 / self.tank_area[tank] <= self.tank_height[tank]
        model.tank_height_limit = pyomo.Constraint(model.tank_set, model.timeperiods, rule=tank_height)


        # Create instance of model
        instance = model.create_instance(data)

        # Fix if required
        # instance.x['crude', 'crude_source', 'ad'].fix(100000)

        # Shutting down reformer for period 4
        # instance.x['srn', 'srn_tk', 'rf', 4].fix(0)
        # instance.x['srn', 'srn_sp', 'rf', 4].fix(0)

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


def main():
    # initialize refinery class
    refinery_problem = RefineryOptimizationAbstract()

    # solve optimization problem
    optimization_result = refinery_problem.execute_optimization()

    # print results using results
    refinery_problem.print_output(optimization_result)


if __name__ == "__main__":
    main()
