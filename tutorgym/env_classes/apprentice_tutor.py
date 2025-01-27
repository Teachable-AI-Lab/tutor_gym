from tutorgym.shared import ProblemState, Action
from shop2.fact import Fact # type: ignore
from .planner import planner
import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from tutorgym.env_classes.env_base import TutorEnvBase
import re



# TODO

def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField"):
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True        
    return next_state


class HTNCognitiveModel:
    def __init__(self, start_state, task, domain):
        self.start_state = ProblemState(start_state)
        self.task = task
        self.domain = domain

    def get_next_actions(self, state):
        state_list: list[dict] = sorted(list(state.objs.values()), key=lambda x: x['y'])
        fact_state: Fact = Fact(start=True) & Fact(scaffold='level_4') & Fact(scaffold='level_3') & Fact(scaffold='level_2') & Fact(scaffold='level_1')       

        answers: list[Fact] = []
        for value in state_list:
            if value['id'] == 'done':
                continue
            if value['id'] != 'equation' and value['locked']:
                answers.append(Fact(field=value['id'], value=value['value'], answer=value['locked']))
            else:
                fact_state = fact_state & Fact(field=value['id'], value=value['value'], answer=value['locked'])
        
        plan = planner(fact_state, self.task, self.domain)
        effect, fact_state = plan.send(None)
        for answer in answers:
            value = answer['value']
            while True:
                exitloop = False
                if effect['value'][0][1] == value and effect['field'] == answer['field']:
                    effect['value'] = answer['value']
                    effect, fact_state = plan.send((fact_state, True, effect))
                    exitloop = True
                    break
                if exitloop:
                    break
                effect, fact_state = plan.send((fact_state, False, effect))
        
        expected: list[Fact] = []

        while True:            
            effect, fact_state = plan.send((fact_state, False, expected))
            if not effect:
                break
            expected.append(effect)
            

        
        next_actions = []
        for effect in expected:
            if effect['field'] == 'done':
                next_actions.append(
                    Action(
                        ('done', 'PressButton', {'value': -1}), 
                        how_str="-1")
                    )
            else:
                next_actions.append(
                    Action(
                        (f'{effect["field"]}', 'UpdateTextField', {'value': effect['value'][0][1]}), 
                        arg_foci=[effect['arg_foci']] if 'arg_foci' in effect else [''],
                        how_str=effect['how'] if 'how' in effect else ''
                    )
                )

        return next_actions


class ApprenticeTutor(TutorEnvBase):
    def create_htn_model(self):
        raise NotImplementedError("Subclass must implement create_htn_model().")
    
    def set_start_state(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement set_start_state().")
    
    def _standardize_config(self, *args, **kwargs):
        problem: str = self.set_start_state
        return {'equation': problem}

    def set_problem(self, *args, **kwargs):
        self.set_start_state(*args, **kwargs)
        self.htn_model = self.create_htn_model(self.start_state)
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
        action = Action(action)
        correct_actions = self.htn_model.get_next_actions(self.state)
        check_args = kwargs.get('check_args', self.check_args)
        check_how = kwargs.get('check_how', self.check_how)
        for ca in correct_actions:
            if ca.is_equal(action, check_args=check_args, check_how=check_how):
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
        correct_actions = self.htn_model.get_next_actions(self.state)
        return self._process_demo(correct_actions[0],**kwargs)
    
    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        correct_actions = self.htn_model.get_next_actions(self.state)
        return [self._process_demo(a, **kwargs) for a in correct_actions]
    