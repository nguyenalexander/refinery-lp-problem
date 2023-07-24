from src.refinery_problem import model
from src.refinery_problem import helpers
from src.case_studies import case_study_01
from src.case_studies import case_study_02
from src.case_studies import case_study_03
from src.case_studies import case_study_04


def main():
    # initialize refinery model and instantiate the model
    refinery_object = model.RefineryModel()
    refinery_problem = refinery_object.build_model()

    # case study 1
    optimization_cs_01 = case_study_01.execute_optimization(refinery_problem)
    # helpers.print_output(optimization_cs_01)

    # # case study 2
    # optimization_cs_02 = case_study_02.execute_optimization(refinery_problem)
    # helpers.print_output(optimization_cs_02)
    #
    # # case study 3
    # optimization_cs_03 = case_study_03.execute_optimization(refinery_problem)
    # helpers.print_output(optimization_cs_03)
    #
    # # case study 4
    # optimization_cs_04 = case_study_04.execute_optimization(refinery_problem)
    # helpers.print_output(optimization_cs_04)


if __name__ == "__main__":
    main()
