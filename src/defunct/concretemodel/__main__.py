import pyomo.environ as pyomo
import numpy as np
import pandas as pd

class RefineryOptimizationConcrete:
    """Class used to create an optimization object, set-up the problem, solve, and output."""
    def __init__(self):
        """Initialization of data sets"""

        # costs for designated streams (operating costs, material cost, product costs)
        self.costs = {
            1: {'cost': -33},
            2: {'cost': 0.01965},
            7: {'cost': 0.01965},
            8: {'cost': -2.5},
            10: {'cost': -2.2},
            12: {'cost': -2.2},
            15: {'cost': 0.01965},
            33: {'cost': 45.36},
            34: {'cost': 43.68},
            35: {'cost': 40.32},
            36: {'cost': 13.14}
        }

        # dictionary of each split origin and the respective split streams
        self.split_list = {
            3: [18, 19],
            4: [8, 9],
            5: [10, 11],
            6: [12, 13],
            14: [20, 21],
            9: [22, 23, 24],
            16: [25,26],
            17: [27, 28],
            11: [29, 30],
            13: [31, 32]
        }

        # yield coefficients for each unit operation
        # Atmospheric Distillation
        self.ad_yield_coef = {
            2: {'yield': 35.42},
            3: {'yield': 0.270},
            4: {'yield': 0.237},
            5: {'yield': 0.087},
            6: {'yield': 0.372}
        }
        # Reformer
        self.rf_yield_coef = {
            7: {'yield': 158.7},
            14: {'yield': 0.928}
        }
        # Catalytic Cracker for SRDS Feed
        self.cc_srds_yield_coef = {
            15: {'yield': 336.9},
            16: {'yield': 0.619},
            17: {'yield': 0.189}
        }
        # Catalytic Cracker for SRFO Feed
        self.cc_srfo_yield_coef = {
            15: {'yield': 386.4},
            16: {'yield': 0.688},
            17: {'yield': 0.2197}
        }

        # Feed Properties for Blending
        # Octane Ratings
        self.octane_rating = {
            18: {'octane': 78.5},
            19: {'octane': 78.5},
            20: {'octane': 104},
            21: {'octane': 104},
            22: {'octane': 65},
            23: {'octane': 65},
            24: {'octane': 65},
            25: {'octane': 93.7},
            26: {'octane': 93.7}
        }
        # Vapour Pressures
        self.vapour_pres = {
            18: {'vpress': 18.4},
            19: {'vpress': 18.4},
            20: {'vpress': 2.57},
            21: {'vpress': 2.57},
            22: {'vpress': 6.54},
            23: {'vpress': 6.54},
            24: {'vpress': 6.54},
            25: {'vpress': 6.9},
            26: {'vpress': 6.9}
        }
        # Densities
        self.density_spec = {
            24: {'density': 272},
            27: {'density': 294.4},
            28: {'density': 294.4},
            29: {'density': 292},
            30: {'density': 292},
            31: {'density': 295},
            32: {'density': 295}
        }
        # Sulfur Concentrations
        self.sulfur_spec = {
            24: {'sulfur': 0.283},
            27: {'sulfur': 0.353},
            28: {'sulfur': 0.353},
            29: {'sulfur': 0.526},
            30: {'sulfur': 0.526},
            31: {'sulfur': 0.980},
            32: {'sulfur': 0.980}
        }

    def build_model(self):
        """
        Build the optimization model with constraints and objectives.
        Returns the Pyomo model object for solving.
        """

        # instantiate a concrete Pyomo model
        model = pyomo.ConcreteModel()
        model.varidx = pyomo.RangeSet(36)
        model.x = pyomo.Var(model.varidx, domain=pyomo.NonNegativeReals)

        # objective function (profit = products - operating cost - crude cost)
        model.cost = pyomo.Objective(expr = sum(model.x[c] * self.costs[c]['cost'] for c in self.costs), sense=pyomo.maximize)

        # used if fixing variables to a VALUE is desired
        # model.x[1].value = 100000
        # model.x[1].fixed = True
        # Alternatively: model.x[1].fix(100000) works
        # model.x[9].fix(0)

        # crude capacity constraint
        model.crudecap = pyomo.Constraint(expr = model.x[1] <= 110000)

        # unit capacity constraints
        model.adcap = pyomo.Constraint(expr = model.x[1] <= 100000)
        model.rfcap = pyomo.Constraint(expr = model.x[8] <= 25000)
        model.cccap = pyomo.Constraint(expr = model.x[10] + model.x[12] <= 30000)

        # volumetric yield equations
        model.ad_yield = pyomo.ConstraintList()
        for y in self.ad_yield_coef:
            model.ad_yield.add(expr = model.x[y] == model.x[1] * self.ad_yield_coef[y]['yield'])

        model.rf_yield = pyomo.ConstraintList()
        for y in self.rf_yield_coef:
            model.rf_yield.add(expr = model.x[y] == model.x[8] * self.rf_yield_coef[y]['yield'])

        model.cc_yield = pyomo.ConstraintList()
        for y in self.cc_srds_yield_coef:
            model.cc_yield.add(expr = model.x[y] == model.x[10] * self.cc_srds_yield_coef[y]['yield'] + model.x[12] * self.cc_srfo_yield_coef[y]['yield'])

        # demand constraints
        model.pg_demand = pyomo.Constraint(expr = model.x[33] >= 10000)
        model.rg_demand = pyomo.Constraint(expr = model.x[34] >= 10000)
        model.df_demand = pyomo.Constraint(expr = model.x[35] >= 10000)
        model.fo_demand = pyomo.Constraint(expr = model.x[36] >= 10000)

        # blend tank balances
        model.pg_blend = pyomo.Constraint(expr = model.x[33] == model.x[18] + model.x[20] + model.x[22] + model.x[25])
        model.rg_blend = pyomo.Constraint(expr = model.x[34] == model.x[19] + model.x[21] + model.x[23] + model.x[26])
        model.df_blend = pyomo.Constraint(expr = model.x[35] == model.x[24] + model.x[27] + model.x[29] + model.x[31])
        model.fo_blend = pyomo.Constraint(expr = model.x[36] == model.x[28] + model.x[30] + model.x[32])

        # quality constraints
        # premium gasoline
        model.pg_octane = pyomo.Constraint(expr = sum(model.x[i] * self.octane_rating[i]['octane'] for i in [18, 20, 22, 25]) - 93 * model.x[33] >= 0)
        model.pg_vpress = pyomo.Constraint(expr = sum(model.x[i] * self.vapour_pres[i]['vpress'] for i in [18, 20, 22, 25]) - 12.7 * model.x[33] <= 0)

        # regular gasoline
        model.rg_octane = pyomo.Constraint(expr = sum(model.x[i] * self.octane_rating[i]['octane'] for i in [19, 21, 23, 26]) - 83 * model.x[34] >= 0)
        model.rg_vpress = pyomo.Constraint(expr = sum(model.x[i] * self.vapour_pres[i]['vpress'] for i in [19, 21, 23, 26]) - 12.7 * model.x[34] <= 0)

        # diesel fuel
        model.df_density = pyomo.Constraint(expr = sum(model.x[i] * self.density_spec[i]['density'] for i in [24, 27, 29, 31]) - 306 * model.x[35] <= 0)
        model.df_sulfur = pyomo.Constraint(expr = sum(model.x[i] * self.sulfur_spec[i]['sulfur'] for i in [24, 27, 29, 31]) - 0.50 * model.x[35] <= 0)

        # fuel oil
        model.fo_density = pyomo.Constraint(expr = sum(model.x[i] * self.density_spec[i]['density'] for i in [28, 30, 32]) - 352 * model.x[36] <= 0)
        model.fo_sulfur = pyomo.Constraint(expr = sum(model.x[i] * self.sulfur_spec[i]['sulfur'] for i in [28, 30, 32]) - 3.0 * model.x[36] <= 0)

        # split point balances
        model.splitbalances = pyomo.ConstraintList()
        for s in self.split_list:
            model.splitbalances.add(model.x[s] == sum(model.x[i] for i in self.split_list[s]))

        model.pprint()
        return model

    def execute_optimization(self):
        """Builds the Pyomo Model then solves the optimization problem. Returns the solved model object."""
        opt_model = self.build_model()
        solver = pyomo.SolverFactory('glpk')
        solver.solve(opt_model, tee=True)

        return opt_model

    def print_output(self, opt_model):
        """Prints the flow rates, then the total profit and production of each product and their properties."""
        for c in opt_model.varidx:
            print(opt_model.x[c])
            print(opt_model.x[c]())

        print('Objective (Cost): ', sum(opt_model.x[c]() * self.costs[c]['cost'] for c in self.costs))

        print('PG Production: ', opt_model.x[33]())
        print('PG Octane: ', sum(opt_model.x[i]() * self.octane_rating[i]['octane'] for i in [18, 20, 22, 25]) / opt_model.x[33]())
        print('PG Vapour Pressure: ', sum(opt_model.x[i]() * self.vapour_pres[i]['vpress'] for i in [18, 20, 22, 25]) / opt_model.x[33]())

        print('RG Production: ', opt_model.x[34]())
        print('RG Octane: ', sum(opt_model.x[i]() * self.octane_rating[i]['octane'] for i in [19, 21, 23, 26]) / opt_model.x[34]())
        print('RG Octane: ', sum(opt_model.x[i]() * self.vapour_pres[i]['vpress'] for i in [19, 21, 23, 26]) / opt_model.x[34]())

        print('DF Production: ', opt_model.x[35]())
        print('DF Density: ', sum(opt_model.x[i]() * self.density_spec[i]['density'] for i in [24, 27, 29, 31]) / opt_model.x[35]())
        print('DF Sulfur: ', sum(opt_model.x[i]() * self.sulfur_spec[i]['sulfur'] for i in [24, 27, 29, 31]) / opt_model.x[35]())

        print('FO Production: ', opt_model.x[36]())
        print('FO Density: ', sum(opt_model.x[i]() * self.density_spec[i]['density'] for i in [28, 30, 32]) / opt_model.x[36]())
        print('FO Sulfur: ', sum(opt_model.x[i]() * self.sulfur_spec[i]['sulfur'] for i in [28, 30, 32]) / opt_model.x[36]())

        opt_model.display()

def main():
    # initialize refinery class
    refinery_problem = RefineryOptimizationConcrete()

    # solve optimization problem
    optimization_result = refinery_problem.execute_optimization()

    # print results using results
    refinery_problem.print_output(optimization_result)


if __name__ == "__main__":
    main()