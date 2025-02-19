import lxml.etree as ET
from tutorgym.shared import Action, ProblemState
from tutorgym.env_classes.fsm_tutor import StateMachineTutor, FiniteStateMachine
from tutorgym.env_classes.env_base import TutorEnvBase
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.env_classes.CTAT.brd_tools import parse_brd
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.html_tools import HTML_Preprocessor
import json
from copy import copy
import re
import os

# -----------------------------------------------------------------
# : Action Filters

def action_not_buggy(action):
    return action.get_annotation("action_type", None) != "Buggy Action"


template_pattern = re.compile("\%\(.*\)\%")
def action_not_template(action):
    inputs = action.sai[2]
    for k,v in inputs.items():
        if(template_pattern.search(str(k)) or
           template_pattern.search(str(v))):
            return False
    return True


# ------------------------------------------------------------------
# : CTAT_Tutor

def ensure_not_early_done_filter(actions):
    # Find the done action
    done_action = None
    for action in actions:
        if(action.sai[0] == "done"):
            done_action = action
            break

    # Check to see if any action in the same group as the done action is 
    #  non-optional
    done_okay = True
    if(done_action is not None):
        done_group = done_action.get_annotation("group", False)
        for action in actions:
            if(action is not done_action and
               action.get_annotation("group", False) == done_group  and
               action.get_annotation("optional", False) == False):
                done_okay = False
                break

    if(done_okay):
        return actions
    else:
        return [a for a in actions if a is not done_action]





class CTAT_Tutor(StateMachineTutor):
    def __init__(self, html_proc_config={"root_dir" : "./"},
                       edge_filters=[action_not_buggy, action_not_template],
                    **kwargs):
        self.html_proc_config = html_proc_config
        self.html_proc = HTML_Preprocessor(**html_proc_config)
        self.edge_filters = edge_filters
        super().__init__(action_model=CTAT_ActionModel,**kwargs)
        self.next_action_filters.append(ensure_not_early_done_filter)

    def _satisfies_filters(self, action):
        for fltr in self.edge_filters:
            # print("SKIPPING ACTION", action, f"Failed filter {fltr.__name__}")
            if(not fltr(action)):
                return False
        return True

    def set_start_state(self, html_path, model_path, **kwargs):
        # Render the HTML converted the DOM to JSON and snap a picture
        configs = self.html_proc.process_htmls(
            [html_path],
            keep_alive=True
        )

        print(html_path)
        print(model_path)

        # Load the HTML converted to JSON
        with open(configs[0]['json_path']) as f:
            start_state = json.load(f)
            self.start_actions, self.edges, self.groups = \
                parse_brd(model_path)

        self.problem_name = os.path.split(model_path)[-1]

        start_state = ProblemState(start_state)
        # Apply any start state messages in the brd 
        for action in self.start_actions:
            start_state = self.action_model.apply(start_state, action, make_copy=False)

        start_state.action_hist = []
        start_state.add_annotations({"is_start": True, "unique_id" : "1"})

        self.start_state = start_state

    def create_fsm(self, start_state, **kwargs):
        fsm = FiniteStateMachine(
            start_state.copy(keep_annotations=True),
            self.action_model
        )

        # Start by indexing sets of edges by by their source node
        edge_dict = {}
        for edge_id, (node_unq_id, next_unq_id, action) in self.edges.items():
            lst = edge_dict.get(node_unq_id, [])
            lst.append((next_unq_id, action))
            edge_dict[node_unq_id] = lst

        # Then expand edges in waves, one frontier at a time.
        #  A frontier is the set of unvisited nodes that were
        #  destinations of a previous wave's expanded edges. 
        frontier = set(["1"])
        covered = set()
        while len(frontier) > 0:
            new_frontier = set()
            for node_unq_id in frontier:
                if(node_unq_id in covered or node_unq_id not in edge_dict):
                    continue 

                node = fsm.nodes[node_unq_id]
                for next_unq_id, action in edge_dict[node_unq_id]:
                    if(not self._satisfies_filters(action)):
                        continue
                    # if(action.get_annotation("action_type", None) == "Buggy Action"):
                    #     continue
                    group_name = action.get_annotation("group", None)
                    if(group_name is not None):
                        group = self.groups[group_name]
                        next_state = fsm.add_unordered(node['state'], group)
                    else:
                        next_state = fsm.add_edge(node['state'], action, 
                            force_unique_id=next_unq_id)

                    # print(node_unq_id, next_unq_id, action.sai)
                    # print(f"{repr(action)}")

                    if(next_state.get_annotation("is_done", False)):
                        continue

                    new_frontier.add(next_unq_id)
                covered.add(node_unq_id)
            frontier = new_frontier

        return fsm

    # def get_problem():
    #     return self.problem

    def action_is_done(self, action):
        if(action.sai[0] == "done"):
            return True
        return False





    



    # def apply(self, state, action, **kwargs):
    #     return self.action_model.apply(state, action)





# parse_brd("AS_3_7_plus_4_7.brd")
# parse_brd("Mathtutor/6_01_HTML/FinalBRDs/Problem1.brd")

if __name__ == '__main__':
    from tutorgym.trainer import Trainer, AuthorTrainer
    from tutorgym.agents.oracle_agent import OracleAgent
    from random import choice



    tutor = CTAT_Tutor(demo_annotations={"src_id", "dest_id", "unique_id"})

    # Values [0]: Incomplete, value of expression matcher requires eval
    # Order  [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_01_HTML/")

    # Values [x]
    # Order [x]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_02_HTML/")

    # Values [0]: Complicated, mostly dynamic
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_05_HTML/")

    # Values [0]: Complicated, mostly dynamic (Highly custom)
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_06_HTML/")

    # Values [x]: 
    # Order [?]: TODO
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_07_HTML/")

    # Values [0]:Complicated, mostly dynamic (Highly custom similar to 05) 
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_08_HTML/")

    # Values [x]:
    # Order [?]: 
    problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_09_HTML/")

    # Values [0]:Complicated, mostly dynamic (Highly custom similar to 05) 
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_10_HTML/")

    # Values [x]:
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_11_HTML/")

    # Values [0]: Expressions: ifThen, isVar, concat
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_14_HTML/")

    # Values [x]: Only simple ExpressionMatches 
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_15_HTML/")

    # Values [-]: Some simple ExpressionMatches, but several hard ones
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_16_HTML/")

    # Values [-]: Number line, seems feasible
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_17_HTML/")

    # Values [-]: Number line, seems feasible 
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_18_HTML/")

    # Values [-]: Number line, but seems feasible 
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_19_HTML/")

    # Values [-]: Number line, uses eval, but feasible 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_20_HTML/")

    # Values [0]: Expressions, and(), rationalEquals, getDivisor
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_21_HTML/")

    # Values [x]: Just ExpressionMatches
    # Order [?]: 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_24_HTML/")

    # Values [0]: Lots of regular expression matches, including regex in selection
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_25_HTML/")

    # Values [0]: Some regular expression matches, including regex in selection
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_26_HTML/")

    # Values [x]: Just ExpressionMatches
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_27_HTML/")

    # Values [-]: Complicated Expressions, but not that complex
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_28_HTML/")

    # Values [x]: All simple values 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_30_HTML/")

    # Values [x]: All simple values # 
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_34_HTML/")

    omit_problems = [
        "../../envs/CTAT/Mathtutor/6_16_HTML/FinalBRDs/18ABC.brd",
        "../../envs/CTAT/Mathtutor/6_16_HTML/FinalBRDs/13ABDE.brd"
    ]

    problems_so_far = []
    for prob_set in problem_sets:
        for problem in prob_set:
            if(problem['model_path'] in omit_problems):
                continue

            problems_so_far.append(problem)
            #ft
             # print(problem)
            
            agent = OracleAgent(tutor)
            trainer = AuthorTrainer(agent, tutor, problem_set=[problem])
            try:
                trainer.start()
            except Exception as e:
                state = tutor.get_state()
                print(problem['html_path'], problem['model_path'])
                print("ACTION HIST")
                for action in state.action_hist:
                    print(action.get_annotation("unique_id"), action)
                # for prob in problems_so_far:
                #     print(prob['html_path'], prob['model_path'])

                tutor.set_problem(**problem)
                for action in state.action_hist:
                    tutor.apply(action)

                state = tutor.get_state()
                actions = tutor.get_all_demos()
                print(actions)

                raise e
            

            # tutor.set_problem(**problem)
            # for i in range(100):
            #     actions = tutor.get_all_demos()
            #     action = actions[0]
            #     # action = choice(actions)#[-1]
            #     # print(action.annotations)
            #     src_id = action.get_annotation("src_id")
            #     dest_id = action.get_annotation("dest_id")
            #     print(f"{src_id},{dest_id}  Apply Action:", str(action))
            #     next_state = tutor.apply(action)
            #     if(next_state.get_annotation("is_done", False) == True):
            #         break

            # break # only first problem


            

    # tutor.set_problem(html_path="../../envs/CTAT/Mathtutor/6_01_HTML/HTML/6.01-4.html",
    #             model_path="../../envs/CTAT/Mathtutor/6_01_HTML/FinalBRDs/Problem10.brd"
    # )

    # tutor.set_problem(html_path="../../envs/CTAT/Mathtutor/6_11_HTML/HTML/6.11.html",
    #             model_path="../../envs/CTAT/Mathtutor/6_11_HTML/FinalBRDs/p21.brd"
    # )


    











