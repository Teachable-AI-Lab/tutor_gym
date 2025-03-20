from pathlib import Path
from tutorgym.env_classes.oatutor import OATutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.envs.CTAT.Mathtutor.env_registry import WORKING_DOMAINS
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.shared import ProblemState
from tutorgym.helpers.make_compl_prof import make_compl_prof
from tutorgym.helpers.collect_problems import collect_oatutor_problems

import random
import json
import os


PROBLEMS_PER_DOMAIN = 2
RANDOM_PROBLEMS = False

if __name__ == "__main__":
    # print(len(WORKING_DOMAINS))
    # raise ValueError()

    # current_dir = Path(__file__).parent
    # # current_dir = Path(__file__).parent
    # # problem_pool_path = current_dir / "ProblemPool"  



    # problem_names_file = '../../envs/oatutor/ProblemNames.txt'
    # with open(problem_names_file, 'r') as file:
    #     domains = [line.strip() for line in file if line.strip()]

    # problem_pool_dir = os.path.join(current_dir, '../../envs/oatutor/ProblemPool')
    # # problems = os.listdir(problem_pool_dir)

    # problem_names = []

    # for domain in domains:
    #     problems = [d for d in os.listdir(problem_pool_dir) 
    #                 if domain in d and os.path.isdir(os.path.join(problem_pool_dir, d))]

    #     if(RANDOM_PROBLEMS):
    #         random.shuffle(problems)

    #     problem_names += problems[:PROBLEMS_PER_DOMAIN]


    # print(problem_names)

    # problem_set = [{"problem_name" : p} for p in problem_names]
    problem_set = collect_oatutor_problems()

    # domain_dirs = [f"../../envs/CTAT/Mathtutor/{d}/" for d in WORKING_DOMAINS]
    # problems = collect_problems(domain_dirs)


    tutor = OATutor()

    # tutor = CTAT_Tutor()#demo_annotations={"src_id", "dest_id", "unique_id"})

    # if(False):
    
    make_compl_prof(tutor, "oa_compl.prof", problem_set, problem_line_limit=40)



# # Read problem names from file
    
    
#     # Loop through each problem
#     for problem_name in problem_names:
#         print(f"\nRunning tutor for problem: {problem_name}")
#         env = OATutor(problem_name=problem_name)
#         agent = OracleAgent(env)
#         trainer = AuthorTrainer(agent, env, n_problems=20)
#         trainer.start()
