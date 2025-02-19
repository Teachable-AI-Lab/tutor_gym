from pathlib import Path
from tutorgym.env_classes.oa_tutors import OATutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.envs.CTAT.Mathtutor.env_registry import WORKING_DOMAINS
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.shared import ProblemState
from tutorgym.env_classes.CTAT.make_compl_prof import collect_problems, make_compl_prof
import random
import json

if __name__ == "__main__":
    # print(len(WORKING_DOMAINS))
    # raise ValueError()

    # current_dir = Path(__file__).parent
    problem_names_file = '../../../tutorgym/envs/oa_tutors/ProblemNames.txt'
    with open(problem_names_file, 'r') as file:
        problem_names = [line.strip() for line in file if line.strip()]

    print(problem_names)

    problems = [{"problem_name" : p} for p in problem_names]

    # domain_dirs = [f"../../envs/CTAT/Mathtutor/{d}/" for d in WORKING_DOMAINS]
    # problems = collect_problems(domain_dirs)


    tutor = OATutor()

    # tutor = CTAT_Tutor()#demo_annotations={"src_id", "dest_id", "unique_id"})

    # if(False):
    
    make_compl_prof(tutor, "oa_compl.prof", problems, problem_line_limit=40)



# # Read problem names from file
    
    
#     # Loop through each problem
#     for problem_name in problem_names:
#         print(f"\nRunning tutor for problem: {problem_name}")
#         env = OATutor(problem_name=problem_name)
#         agent = OracleAgent(env)
#         trainer = AuthorTrainer(agent, env, n_problems=20)
#         trainer.start()
