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

        # Apply any start state messages in the brd 
        for action in self.start_actions:
            start_state = self.action_model.apply(start_state, action, make_copy=False)
        start_state.action_history = []

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
                if(node_unq_id in covered):
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


                    next_state = fsm.add_edge(node['state'], action, 
                        force_unique_id=next_unq_id)

                    # print(node_unq_id, next_unq_id, action.sai)
                    print(f"{repr(action)}")

                    if(next_state.get_annotation("is_done", False)):
                        continue

                    new_frontier.add(next_unq_id)
                covered.add(node_unq_id)
            frontier = new_frontier

        return fsm



    



    # def apply(self, state, action, **kwargs):
    #     return self.action_model.apply(state, action)





# parse_brd("AS_3_7_plus_4_7.brd")
# parse_brd("Mathtutor/6_01_HTML/FinalBRDs/Problem1.brd")

if __name__ == '__main__':

    tutor = CTAT_Tutor()
    # problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/6_16_HTML/")
    # for prob_set in problem_sets:
    #     for problem in prob_set:
    #         tutor.set_problem(**problem)

    tutor.set_problem(html_path="../../envs/CTAT/Mathtutor/6_11_HTML/HTML/6.11.html",
                model_path="../../envs/CTAT/Mathtutor/6_11_HTML/FinalBRDs/p21.brd"
    )


    for i in range(100):
        print("-- STEP", i, "--")
        actions = tutor.get_all_demos()
        # for action in actions:
        print("Apply Action:", actions[0])

        tutor.apply(actions[0])
        print()











