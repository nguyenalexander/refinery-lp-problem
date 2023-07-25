from src.refinery_problem import model
from src.refinery_problem import helpers
from src.case_studies import case_study_01
from src.case_studies import case_study_02
from src.case_studies import case_study_03
from src.case_studies import case_study_04
from src.case_studies import case_study_05
from src.case_studies import case_study_06
from src.case_studies import case_study_07
import matplotlib.pyplot as plt


def main():
    # initialize refinery model and instantiate the models
    refinery_object = model.RefineryModel()
    refinery_problem_cs_01 = refinery_object.build_model()
    refinery_problem_cs_02 = refinery_object.build_model()
    refinery_problem_cs_03 = refinery_object.build_model()
    refinery_problem_cs_04 = refinery_object.build_model()
    refinery_problem_cs_05 = refinery_object.build_model()
    refinery_problem_cs_06 = refinery_object.build_model()
    refinery_problem_cs_07 = refinery_object.build_model()

    # case study 1
    optimization_cs_01, cs_01_results_df = case_study_01.execute_optimization(refinery_problem_cs_01)
    cs_01_results_df.to_csv('./results/case_study_01.csv', index=True, header=True)

    # case study 2
    optimization_cs_02, cs_02_results_df = case_study_02.execute_optimization(refinery_problem_cs_02)
    cs_02_results_df.to_csv('./results/case_study_02.csv', index=True, header=True)

    # case study 3
    optimization_cs_03, cs_03_results_df = case_study_03.execute_optimization(refinery_problem_cs_03)
    cs_03_results_df.to_csv('./results/case_study_03.csv', index=True, header=True)

    # case study 4
    optimization_cs_04, cs_04_results_df = case_study_04.execute_optimization(refinery_problem_cs_04)
    cs_04_results_df.to_csv('./results/case_study_04.csv', index=True, header=True)

    # case study 5
    optimization_cs_05, cs_05_results_df = case_study_05.execute_optimization(refinery_problem_cs_05)
    cs_05_results_df.to_csv('./results/case_study_05.csv', index=True, header=True)

    # case study 6
    optimization_cs_06, cs_06_results_df = case_study_06.execute_optimization(refinery_problem_cs_06)
    cs_06_results_df.to_csv('./results/case_study_06.csv', index=True, header=True)

    # case study 7
    optimization_cs_07, cs_07_results_df = case_study_07.execute_optimization(refinery_problem_cs_07)
    cs_07_results_df.to_csv('./results/case_study_07.csv', index=True, header=True)


if __name__ == "__main__":
    main()
