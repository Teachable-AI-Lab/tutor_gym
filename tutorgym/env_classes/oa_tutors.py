from tutorgym.envs.oa_tutors.ProblemProcesser import process_problem_pool
from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.env_base import TutorEnvBase
import re

def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField"):
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True
    elif action_type == "UpdateRadioButton":
        step_number = selection.split('_')[0]
        print("selection", selection)
        next_state[selection]['value'] = True
        for key in next_state.objs.keys():
            if key.startswith(step_number):
                next_state[key]['locked'] = True
                next_state[key]['value'] = False

    print("next_state", next_state.objs)
    return next_state

class CogModel:
    def __init__(self, start_state, action_list):
        self.start_state = ProblemState(start_state)
        self.action_list = action_list  

    def get_next_actions(self, state):
        step_keys = [
            key for key in state.objs.keys()
            if re.match(r'step\d+_', key) and 
            not state.objs[key]['locked']
        ]
        
        # Sort keys based on step number
        sorted_keys = sorted(step_keys, 
            key=lambda x: int(re.match(r'step(\d+)_', x).group(1))
        )
        

        if len(sorted_keys) == 0:
            return [Action(('done', 'PressButton', {'value': -1}))]

        answer_key, answer_type = sorted_keys[0].split('_')
        return [
            Action((sorted_keys[0],
                   "UpdateRadioButton" if "choice" in answer_type else "UpdateTextField",
                   {"value": self.action_list[answer_key]}),
                   how_str=state.objs[f"{answer_key}_title"]['value']
            )
        ]

class OATutor(TutorEnvBase):
    def __init__(self, problem_name:str, **kwargs):
        super().__init__(**kwargs)     
        self.problem_name = problem_name        
        self.set_random_problem()

    def set_random_problem(self):
        self.problem_state, self.action_list = process_problem_pool(self.problem_name)
        for key, value in self.problem_state.items():
            self.problem_state[key]['id'] = key
        self.set_problem(self.problem_state['title']['value'])

    def create_cog_model(self, state):
        curr_state = state.copy()
        print("curr_state", curr_state.objs)
        return CogModel(curr_state, self.action_list)
    
    def set_start_state(self, *args, **kwargs):
        ''' Domain implementation: Used by ApprenticeTutor.set_problem() 
            to initialize a start state.'''
        step_fields = [self.problem_state[k]['field'] for k in self.problem_state.keys() if k.startswith('step')]
        self.possible_selections = step_fields
        self.possible_args = step_fields
        self.start_state = ProblemState(self.problem_state)
    
    def _standardize_config(self, *args, **kwargs):
        problem: str = self.set_start_state
        return {'problem': problem}

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
        return self.state.objs
    
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
    