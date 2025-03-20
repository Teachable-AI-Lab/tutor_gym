from tutorgym.envs.oatutor.ProblemProcesser import process_problem_pool
from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.env_base import TutorEnvBase
import re
import os
import inspect
import random

def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField"):
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True
    elif action_type == "UpdateRadioButton":
        step_number = selection.split('_')[0]
        next_state[selection]['value'] = True
        for key in next_state.objs.keys():
            if key.startswith(step_number):
                next_state[key]['locked'] = True
    return next_state

class CogModel:
    def __init__(self, start_state, step_actions):
        self.start_state = ProblemState(start_state)
        self.step_actions = step_actions  
        # print("action_list:", self.action_list)

    def get_next_actions(self, state):

        # Get all unlocked fields like step0, step1, etc. 
        step_keys = [
            key for key in state.objs.keys()
            if re.match(r'step\d+_', key) and 
            not state.objs[key]['locked']
        ]

        # If no unlocked step fields return 'done'
        if len(step_keys) == 0:
            return [Action(('done', 'PressButton', {'value': -1}))]
        
        # Sort keys based on step number to find min unlocked step
        sorted_keys = sorted(
            [(int(re.match(r'step(\d+)_', x).group(1)), x) for x in step_keys]
        )
        min_unlocked_step = f'step{sorted_keys[0][0]}'

        return self.step_actions[min_unlocked_step]




class OATutor(TutorEnvBase):
    def __init__(self, **kwargs):
        
        self_dir, _ = os.path.split(__file__)
        domain_names_path = os.path.join(self_dir, '../../envs/oatutor/ProblemNames.txt')
        with open(domain_names_path, 'r') as file:
            self.domains = [line.strip() for line in file if line.strip()]

        problem_pool_dir = os.path.join(self_dir, '../../envs/oatutor/ProblemPool')

        self.problem_domains = {}
        self.domain_problems = {}
        for domain in self.domains:
            problems = [d for d in os.listdir(problem_pool_dir) 
                        if domain in d and os.path.isdir(os.path.join(problem_pool_dir, d))]
            self.domain_problems[domain] = problems
            for problem in problems:
                self.problem_domains[problem] = domain

        # if not matching_dirs:
        #     print(f"No directories found containing '{problem_name}'")
        #     return

        # print(self.problem_names)

        super().__init__(**kwargs)

        # self.set_random_problem(domain)
            

    def set_random_problem(self, domain=None):
        if(domain is None):
            problem_name = random.choice(list(self.problem_domains.keys()))
        else:
            problem_name = random.choice(self.domain_problems[domain])

        self.set_problem(problem_name)
        # self.problem_state, self.action_list = process_problem_pool(self.problem_name)
        # self.set_problem(self.problem_state['title']['value'])

    def create_cog_model(self, state):
        curr_state = state.copy()
        return CogModel(curr_state, self.step_actions)
    
    def set_start_state(self, problem_name, **kwargs):
        ''' Domain implementation: Used by ApprenticeTutor.set_problem() 
            to initialize a start state.'''
        self.problem_name = problem_name
        self.problem_state, self.step_actions = process_problem_pool(self.problem_name)
        self.domain = self.problem_domains[problem_name]
        # print(self.problem_state)

        for key, obj in self.problem_state.items():
            obj['id'] = key

        step_fields = [self.problem_state[k]['field'] for k in self.problem_state.keys() if k.startswith('step')]
        self.possible_selections = step_fields
        self.possible_args = step_fields
        self.start_state = ProblemState(self.problem_state, step_ind=0)
    
    def _standardize_config(self, *args, **kwargs):
        sig = inspect.signature(self.set_start_state)
        
        problem_config = {}
        for (arg_name, arg) in zip(sig.parameters, args):
            problem_config[arg_name] = arg

        return {**problem_config, **kwargs}

    def set_problem(self, *args, **kwargs):
        self.set_start_state(*args, **kwargs)
        self.cog_model = self.create_cog_model(self.start_state)
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
        return self.state
    
    def set_state(self, objs):
        self.state = ProblemState(objs)
        self.is_done = False

    def check(self, action):
        """ Returns 1 for correct next-step Actions, -1 for incorrect ones."""
        action = Action(action)
        correct_actions = self.cog_model.get_next_actions(self.state)
        for ca in correct_actions:
            if ca.is_equal(action):
                return 1
        return -1
    
    def sai_makes_done(self, sai):
        return sai[0] == 'done'
    
    def apply(self, action):
        """ Applies an Action. Modifying self.state. """
        if (self.sai_makes_done(action.sai)):
            self.is_done = True
            self.state = ProblemState({})
        else:
            self.state = make_next_state(self.state, action.sai)
        return self.state
    
    def _process_demo(self, action, **kwargs):
        action = Action(action.sai, 
                **{k:v for k,v in action.annotations.items() if k in self.demo_annotations
                })
        return action
    
    def get_demo(self, state=None, **kwargs):
        """ Returns a correct next-step Action """
        state = self.state if state is None else state
        correct_actions = self.cog_model.get_next_actions(self.state)
        return self._process_demo(correct_actions[0],**kwargs)
    
    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        correct_actions = self.cog_model.get_next_actions(self.state)
        return [self._process_demo(a, **kwargs) for a in correct_actions]
    
    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args
    
