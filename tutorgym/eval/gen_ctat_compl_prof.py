from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.envs.CTAT.Mathtutor.env_registry import WORKING_DOMAINS
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.shared import ProblemState
from tutorgym.helpers.make_compl_prof import make_compl_prof
from tutorgym.helpers.collect_problems import collect_ctat_problems
import random
import json

if __name__ == "__main__":
    # print(len(WORKING_DOMAINS))
    # raise ValueError()

    domain_dirs = [f"../envs/CTAT/Mathtutor/{d}/" for d in WORKING_DOMAINS]
    problems = collect_ctat_problems(domain_dirs)
    tutor = CTAT_Tutor()#demo_annotations={"src_id", "dest_id", "unique_id"})

    # if(False):
    
    make_compl_prof(tutor, "ctat_small_compl.prof", problems, problem_line_limit=20)
