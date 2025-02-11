from tutorgym.shared import ProblemState, Action
from shop2.fact import Fact # type: ignore
from .planner import planner
import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from tutorgym.env_classes.env_base import TutorEnvBase
import re
import inspect



# TODO

def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField" or action_type == "input change"):
        next_state[selection] = next_state.objs.get(selection, {})
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True        
    return next_state


class HTNCognitiveModel:
    def __init__(self, start_state, task, domain):
        self.start_state = ProblemState(start_state)
        self.task = task
        self.domain = domain

    def get_expected_effects(self, state):
        state_list: list[dict] = sorted(list(state.objs.values()), key=lambda x: x['y'])
        fact_state: Fact = (Fact(start=True)  
         & Fact(scaffold='level_1') & Fact(scaffold='level_2') & Fact(scaffold='level_3') 
         & Fact(scaffold='level_4') & Fact(scaffold='level_5') & Fact(scaffold='level_6')
        )

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
        # fail = False
        #print(answers)
        for answer in answers:            
            value = answer['value']
            while True:                
                exitloop = False

                # if(effect is False):
                #     fail = True
                #     break

                for evalue in effect['value']:
                    if(effect['field'] != answer['field']):
                        print("NOMATCH(FIELD) :",  answer['field'], "->", f"{value}", f"{answer['field']}!={effect['field']}")
                        continue

                    val_match = evalue[1] == value
                    if(not val_match):
                        sympy_value = re.sub(r'sqrt(\d+)', r'sqrt{\1}', value)
                        sympy_value = sp.sstr(parse_latex(sympy_value), order='grlex')
                        sympy_value = sympy_value.replace('-1*s', '-s').replace('-1*l', '-l').replace('-1*e', '-e')
                        val_match = evalue[0] == sympy_value or evalue[0].match(sympy_value) is not None

                        if(not val_match):
                            #print("EVALUE[0]", evalue[0], evalue[0].match(value) is not None)
                            #print("EVALUE[1]", effect['field'], "->", evalue[1], evalue[1] == value)
                            print("NOMATCH(VALUE):",  answer['field'], "->", f"{sympy_value}", evalue[0])
                    
                    if val_match:
                        effect['value'] = answer['value']
                        effect, fact_state = plan.send((fact_state, True, effect))
                        exitloop = True
                        break
                if exitloop:
                    break
                effect, fact_state = plan.send((fact_state, False, effect))
        
        expected: list[Fact] = []

        # while not fail:            
        while True:            
            effect, fact_state = plan.send((fact_state, False, expected))
            #print("EFFECT", effect)
            if not effect:
                break
            expected.append(effect)

        return expected

    def effect_to_action(self, effect):
        if effect['field'] == 'done':
            action = Action(
                    ('done', 'PressButton', {'value': -1}), 
                    how_str="-1")
                
        else:
            #value = str(parse_latex(effect['value'][0][1]))
            value = effect['value'][0][1]

            action = Action(
                (f'{effect["field"]}', 'input change', {'value': value}), 
                arg_foci=[effect['arg_foci']] if 'arg_foci' in effect else [''],
                how_str=effect['how'] if 'how' in effect else '',
            )

        return action

    # def action_to_effect(self, action):
    #     return {
    #         "field" : action.sai[0],
    #         "    action.sai[1],
    #         "value" : action.sai[2]
    #     }
            

    def get_next_actions(self, state):
        expected = self.get_expected_effects(state)
        
        next_actions = []
        for effect in expected:
            next_actions.append(self.effect_to_action(effect))

        return next_actions


class ApprenticeTutor(TutorEnvBase):
    def create_htn_model(self):
        raise NotImplementedError("Subclass must implement create_htn_model().")
    
    def set_start_state(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement set_start_state().")
    
    def _standardize_config(self, *args, **kwargs):
        sig = inspect.signature(self.set_start_state)
        
        problem_config = {}
        for (arg_name, arg) in zip(sig.parameters, args):
            problem_config[arg_name] = arg

        return {**problem_config, **kwargs}

    def set_problem(self, *args, **kwargs):
        self.set_start_state(*args, **kwargs)
        self.htn_model = self.create_htn_model(self.start_state)
        self.state = self.start_state

        self.problem_config = self._standardize_config(*args, **kwargs)
        # print("problem_config", self.problem_config)
    
    def get_problem(self):
        return getattr(self, 'problem_name', self.problem_config)

    def get_problem_config(self):
        return self.problem_config
    
    def reset(self):
        self.state = self.start_state.copy()

    def get_state(self):
        return self.state
    
    def set_state(self, objs):
        self.state = ProblemState(objs)

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
            self.state = ProblemState({}, is_done=True)
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
        correct_actions = self.htn_model.get_next_actions(self.state)
        return self._process_demo(correct_actions[0],**kwargs)
    
    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        correct_actions = self.htn_model.get_next_actions(self.state)
        return [self._process_demo(a, **kwargs) for a in correct_actions]


    
