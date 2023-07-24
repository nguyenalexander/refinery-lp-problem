from src.refinery_problem import model
from src.refinery_problem import helpers


def main():
    # initialize refinery model and instantiate the model
    refinery_object = model.RefineryModel()
    refinery_problem = refinery_object.build_model()

    # solve optimization problem
    optimization_result = helpers.execute_optimization(refinery_problem)

    # print results
    helpers.print_output(optimization_result)


if __name__ == "__main__":
    main()
