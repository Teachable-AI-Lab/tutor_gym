from itertools import permutations
import numpy as np
import json
from tutorgym.utils import unique_hash
from tutorgym.shared import ProblemState, Action
import inspect
from abc import ABC, abstractmethod
from tutorgym.env_classes.env_base import TutorEnvBase

# ----------------------------------------------------------------
# : StateMachineTutor Tutor

# TODO: Should reuse the predict_next_state() machinery in cre_agent 
#  to implement this.
def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField"):
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True        
    return next_state

class FiniteStateMachine:
    def __init__(self, start_state):
        self.start_state = ProblemState(start_state)
        self.nodes = {}
        self._ensure_node(start_state)

    def _ensure_node(self, state):
        if(state not in self.nodes):
            self.nodes[state] = {
                "state" : state,
                "edges" : {}
            }
        return self.nodes[state]

    def add_edge(self, state, action, is_done=False):
        action = Action(action) # Standardize
        state = ProblemState(state)
        node = self._ensure_node(state)
        if(is_done):
            next_state = ProblemState({})
        else:
            next_state = make_next_state(state, action.sai)
        node['edges'][action] = next_state
        self._ensure_node(next_state)
        return next_state

    def add_unordered(self, state, action_list):
        action_list = [Action(x) for x in action_list] # Standardize
        start_state = ProblemState(state)
        for ordered in permutations(action_list):
            state = start_state
            for action in ordered:
                state = self.add_edge(state, action)
        return state # State after unordered actions

    def get_next_actions(self, state):
        out_edges = self.nodes[state]['edges']
        return list(out_edges.keys())

    # def copy(self, omit_action_parts=[]):
    #     new_fsm = FiniteStateMachine(self.start_state)
    #     for state, node in new_fsm.nodes.items():
    #         new_node = new_fsm._ensure_node(state)
    #         new_edges = {}
    #         for action, next_state in node['edges'].items():
    #             action_copy = action.copy(omit_action_parts)
    #             new_edges[action_copy] = next_state
    #         new_node['edges'] = new_edges
    #         new_fsm.nodes[state] = new_node
    #     return new_fsm


def load_fsm(file_path):
    ''' Load a finite state machine from a brd or json file.'''
    raise NotImplementedError


class StateMachineTutor(TutorEnvBase):
    def create_fsm(self):
        raise NotImplementedError("Subclass must implement create_fsm().")
            
    def set_start_state(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement set_start_state().")

    def _standardize_config(self, *args, **kwargs):
        sig = inspect.signature(self.set_start_state)

        problem_config = {}
        for (arg_name, arg) in zip(sig.parameters, args):
            problem_config[arg_name] = arg

        return {**problem_config, **kwargs}

    def set_problem(self, *args, **kwargs):
        # subclasses defined start state
        self.set_start_state(*args, **kwargs)
        # subclasses defined fsm constructor
        self.fsm = self.create_fsm(self.start_state)
        self.state = self.start_state
        self.is_done = False

        self.problem_config = self._standardize_config(*args, **kwargs)
        

    def get_problem(self):
        return getattr(self, 'problem_name', self.problem_config)

    def get_problem_config(self):
        return self.problem_config

    def reset(self):
        self.state = self.start_state.copy()
        self.is_done = False

    def get_state(self):
        return self.state.objs

    def set_state(self, objs):
        self.state = ProblemState(objs)
        self.is_done = False

    def check(self, action, **kwargs):
        """ Returns 1 for correct next-step Actions, -1 for incorrect ones."""
        action = Action(action) # standardize
        correct_actions = self.fsm.get_next_actions(self.state)

        # print("CHECK:", repr(action), correct_actions)
        check_args = kwargs.get('check_args',self.check_args)
        check_how = kwargs.get('check_how',self.check_how)
        for ca in correct_actions:
            if(ca.is_equal(action, check_args=check_args, check_how=check_how)):
                return 1
        return -1

    def sai_makes_done(self, sai):
        return sai[0] == 'done'

    # def _action_to_sai(self, action):
    #     if(not isinstance(action, (SAI, tuple, list, dict))):
    #         if(hasattr(action, 'sai')):
    #             sai = SAI(*action.sai)
    #         else:
    #             raise ValueError(f"Action {action} does not have .sai property.")
    #     else:
    #         sai = SAI(action)
    #     return sai

    def apply(self, action):
        """ Applies an Action. Modifying self.state. """
        # sai = self._action_to_sai(action)
        if(self.sai_makes_done(action.sai)):
            self.is_done = True
            self.state = ProblemState({})
        else:
            self.state = make_next_state(self.state, action.sai)
        return self.state.objs

    def _process_demo(self, action, **kwargs):
        # demo_args = kwargs.get('demo_args',self.demo_args)
        # demo_how = kwargs.get('demo_how',self.demo_how)
        # print("PROCESS", demo_how, demo_args)
        # if(not demo_args or not demo_how):
        action = Action(action.sai, 
                **{k:v for k,v in action.annotations.items() if k in self.demo_annotations
                })
        # action = action.copy(ommit_annotations=not demo_args, omit_how=not demo_how)
        return action

    def get_demo(self, state=None, **kwargs):
        """ Returns a correct next-step Action """
        state = self.state if state is None else state
        correct_actions = self.fsm.get_next_actions(self.state)
        return self._process_demo(correct_actions[0],**kwargs)

    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        correct_actions = self.fsm.get_next_actions(self.state)
        # print("DEMOS:")
        # for a in correct_actions:
        #     print('\t', repr(a))
        return [self._process_demo(a, **kwargs) for a in correct_actions]

    
