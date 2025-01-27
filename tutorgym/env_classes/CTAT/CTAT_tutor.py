import lxml.etree as ET
from tutorgym.shared import Action
from tutorgym.env_classes.fsm_tutor import StateMachineTutor
from tutorgym.env_classes.env_base import TutorEnvBase
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.env_classes.CTAT.brd_tools import parse_brd
from tutorgym.html_tools import HTML_Preprocessor


# ------------------------------------------------------------------
# .brd parsing tools

class CTAT_Tutor(StateMachineTutor):
    def __init__(self, html_proc_config={"keep_alive":True}):
        self.html_proc_config 
        self.html_proc = HTML_Preprocessor(**html_proc_config)

    def create_fsm(self, start_state, **kwargs):
        pass

    def set_start_state(self, html_path, model_path, **kwargs):


        
        




    # def set_problem(self, html_path, brd_path, *args, **kwargs):

    # def get_problem(self):

    # def get_problem_config(self):

    # def get_demo(self, state=None, **kwargs):

    # def get_all_demos(self, state=None, **kwargs):

    # def check(self, action, **kwargs):

    # def get_state(self):

    # def set_state(self, state):

    # def apply(self, action):



        # print("  ", child, child.tag)

# parse_brd("AS_3_7_plus_4_7.brd")
# parse_brd("Mathtutor/6_01_HTML/FinalBRDs/Problem1.brd")

if __name__ == '__main__':

    tutor = CTAT_Tutor()
    problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/")
    for prob_set in problem_sets:
        for problem in prob_set:
            tutor.set_problem(**problem)






