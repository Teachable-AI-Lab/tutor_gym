from pathlib import Path
from tutorgym.shared import ProblemState, Action
from shop2.fact import Fact # type: ignore
from .planner import planner
import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from tutorgym.env_classes.env_base import TutorEnvBase
import re
import inspect
from bs4 import BeautifulSoup

# from tutorgym.shared import ProblemState
# from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor, HTNCognitiveModel
from shop2.domain import Task
from copy import deepcopy
from shop2.conditions import AND



# TODO

def make_next_state(state, sai, reward=1):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField" or action_type == "input change"):
        next_state[selection] = next_state.objs.get(selection, {})
        next_state[selection]['value'] = inputs['value']
        if(reward == 1):
            next_state[selection]['locked'] = True
        else:
            next_state[selection]['locked'] = False
    return next_state


def check_effect_match(effect, answer, verbosity=1):
    value = answer['value']

    if(effect['field'] != answer['field']):
        if(verbosity >= 1):
            print("NOMATCH(FIELD) :",  answer['field'], "->", f"{value}", f"{answer['field']}!={effect['field']}")
        return False

    val_match = False

    # EDGE CASE: Pressing done, it doesn't matter what the input value is, just field.
    if(effect['field'] == "done"):
        return True

    for evalue in effect['value']:
        val_match = False
        # Check if the hint demo (which is usually a fixed latex string) equals the answer value
        if(len(evalue) >= 2):
            val_match = evalue[1] == value

        # Otherwise convert from latex to a standard sympy string and see if either 
        # matcher string (which is usually a regex over sympy strings) or the regex matches         
        if(not val_match):
            sympy_value = re.sub(r'sqrt(\d+)', r'sqrt{\1}', value)
            sympy_value = sp.sstr(parse_latex(sympy_value), order='grlex')
            sympy_value = sympy_value.replace('-1*s', '-s').replace('-1*l', '-l').replace('-1*e', '-e')

            val_match = (evalue[0] == sympy_value or 
                         evalue[0].match(sympy_value) is not None)

        if(val_match):
            return True
        else:
            #print("EVALUE[0]", evalue[0], evalue[0].match(value) is not None)
            #print("EVALUE[1]", effect['field'], "->", evalue[1], evalue[1] == value)
            if(verbosity >= 1):
                print("NOMATCH(VALUE):",  answer['field'], "->", f"{sympy_value}", evalue[0])
    return val_match


def effect_to_action(effect):
    if effect['field'] == 'done':
        action = Action(
                ('done', 'PressButton', {'value': -1}), 
                how_str="-1")
            
    else:
        #value = str(parse_latex(effect['value'][0][1]))
        value = str(effect['value'][0][1])

        action = Action(
            (f'{effect["field"]}', 'input change', {'value': value}), 
            arg_foci=[effect['arg_foci']] if 'arg_foci' in effect else [''],
            how_str=effect['how'] if 'how' in effect else '',
        )

    return action

def action_to_answer(action):
    selection, action_type, inputs = action.sai

    if selection == 'done':
        answer = {
            "field" : "done",
            "action" : "button click",
            "value" : "x"
        }
    else:
        #value = str(parse_latex(effect['value'][0][1]))
        answer = {
            "field" : selection,
            "action" : action_type,
            "value" : inputs['value']
        }
    return answer
            



class HTNCognitiveModel:
    def __init__(self, start_state, task, domain, scaffold="all"):
        self.start_state = ProblemState(start_state)
        self.task = task
        self.domain = domain
        self.scaffold = scaffold

    def get_expected_effects(self, state):
        state_list: list[dict] = sorted(list(state.objs.values()), key=lambda x: x['y'])
        fact_state: Fact = Fact(start=True)  

        # print(">>>", self.domain['solve'])

        if(self.scaffold == "all"):
            # print("SCAFFOLD", self.scaffold)
            fact_state = (fact_state 
             & Fact(scaffold='level_0') & Fact(scaffold='level_1')
             & Fact(scaffold='level_2') & Fact(scaffold='level_3') 
             & Fact(scaffold='level_4') & Fact(scaffold='level_5') 
             & Fact(scaffold='level_6')
            )
        elif self.scaffold is not None:
            fact_state = fact_state & Fact(scaffold=self.scaffold)
        

        answers: list[Fact] = []
        for value in state_list:
            if value['id'] == 'done' or 'label' in value['id']:
                continue
            
            if value['id'] != 'equation' and value['locked']:
                answers.append(Fact(field=value['id'], value=value['value'], answer=value['locked']))
            else:
                fact_state = fact_state & Fact(field=value['id'], value=value['value'], answer=value['locked'])
        
        # print("FS", fact_state)

        plan = planner(fact_state, self.task, self.domain)        
        effect, fact_state = plan.send(None)
        # fail = False
        
        # Get the planner caught up with the previous answers
        for answer in answers:            
            i = 0
            while True:                
                if effect and check_effect_match(effect, answer):
                    effect['value'] = answer['value']
                    effect, fact_state = plan.send((fact_state, True, effect))
                    break

                # NOTE: Danny's kludgey fail-safe, not clear why planner
                #  gets stuck in infinite loop here
                i += 1
                if(i == 10):
                    break
                    #raise RuntimeError()

                # print("EEE", effect)
                # print(fact_state)
                next_effect, fact_state = plan.send((fact_state, False, effect))
                # if(next_effect and effect and next_effect == effect):
                #     break
                effect = next_effect
        
        expected: set[Fact] = set()

        # while not fail:            
        while True:            
            effect, fact_state = plan.send((fact_state, False, expected))
            # print("EFFECT", effect)
            if not effect:
                break
            expected.add(effect)

        return list(expected)

    

    

    def get_next_actions(self, state):
        expected = self.get_expected_effects(state)
        
        next_actions = []
        for effect in expected:
            next_actions.append(effect_to_action(effect))

        return next_actions


class ApprenticeTutor(TutorEnvBase):
    def __init__(self, domain, problem_generator, problem_types="power", scaffold="first", **kwargs):
        super().__init__(**kwargs)        
        self.problem_types = problem_types
        self.domain = deepcopy(domain)

        self._resolve_scaffold_options()
        

        if(scaffold == "first"):
            scaffold = list(self.scaffold_options)[0]

            # precond = self.domain['solve'].preconditions[0]
            # if(not isinstance(precond, AND)):
            #     precond = AND(precond)

            # for cond in precond:
            #     print("cond", cond)
            #     scaffold = cond.get('scaffold', None)
            #     if(scaffold is not None):
            #         continue

        # self.domain['solve'].preconditions = [self.domain['solve'].preconditions[0]]
        # self.domain['solve'].subtasks = [self.domain['solve'].subtasks[0]]


        self.problem_generator = problem_generator
        self.scaffold = scaffold
        self.set_random_problem()

    # def __init__(self, scaffold="all", **kwargs):
    #     self.scaffold = scaffold
    #     super().__init__(self,**kwargs)

    def _resolve_scaffold_options(self):
        self.scaffold_options = []
        for precond in self.domain['solve'].preconditions:
            if(not isinstance(precond, AND)):
                precond = AND(precond)
        
            scaffold = None
            for cond in precond:
                scaffold = cond.get('scaffold', None)
                if(scaffold is not None):
                    break
            self.scaffold_options.append(scaffold)
        print("scaffold_options", self.scaffold_options)
        return self.scaffold_options

    def _blank_state(self, type):
        current_dir = Path(__file__).parent.parent
        html_path = f"{current_dir}/envs/apprentice_tutors/static_html/{type}.html"
        with open(html_path, 'r') as file:
            soup = BeautifulSoup(file, 'html.parser')
            
        field_params = {'type': 'TextField', 'value' : "", 'width' : 100, 'height' : 50,  }
        label_params = {'type': 'Label', 'width' : 100, 'height' : 50, 'locked': True, }
        button_params = {'x': 0, 'type': 'Button', 'width' : 100, 'height' : 50, }

        field_names = [x.name for x in self.domain['solve'].subtasks[0]]        

        state: dict = { 'equation' : {'y': 10, 'locked': False,  **field_params}}
        row_count: dict[str, int] = {'factor_1_b': 1, 'factor_2_b': 1, 'sum_factor': 1, 'sum_c': 1}
        for idx, field in enumerate(field_names):            
            if field == 'done':
                state[field] = {'y': 10 + (idx + 1) * 100, **button_params}
            else:
                # Check if field matches special patterns that need row count
                if (field.startswith(('factor_1_b', 'factor_2_b', 'sum_factor', 'sum_c'))):
                    field_id = f'{field}_{row_count[field]}'
                    label_elem = soup.find(id=field_id).find_previous_sibling('label')
                    if not label_elem:
                        label_elem = soup.find(id=field_id).find_previous_sibling('p')
                    row_count[field] += 1
                else:
                    field_id = field
                    label_elem = soup.find(id=field).find_previous_sibling('label')
                    if not label_elem:
                        label_elem = soup.find(id=field).find_previous_sibling('p')
                
                label_text = label_elem.text if label_elem else field
                state[f'label_of_{field}'] = {'x': 0, 'y': 10 + (idx + 1) * 100, 'value': label_text, **label_params}
                state[field] = {'x': 200, 'y': 10 + (idx + 1) * 100, 'locked': False,  **field_params}
        for key, value in state.items():
            state[key]['id'] = key        

        self.possible_selections = [x.name for x in self.domain['solve'].subtasks[0]]
        self.possible_args = ['equation', *self.possible_selections[:-2]]

        return ProblemState(state)                

    def set_start_state(self, initial_problem, **kwargs):
        ''' Domain implementation: Used by ApprenticeTutor.set_problem() 
            to initialize a start state.'''

        #print(args, kwargs)
        state = self._blank_state(self.problem_types)
        self.problem = initial_problem
        state['equation']['value'] = self.problem
        self.start_state = ProblemState(state)
    
    def set_random_problem(self):
        equation: str = self.problem_generator()
        self.set_problem(equation)

    def create_htn_model(self, state):
        curr_state = state.copy()
        task = [Task(head=('solve','equation'), primitive=False)]
        return HTNCognitiveModel(curr_state, task, self.domain, scaffold=self.scaffold)
    
    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args
    
    def _standardize_config(self, *args, **kwargs):
        sig = inspect.signature(self.set_start_state)
        
        problem_config = {}
        for (arg_name, arg) in zip(sig.parameters, args):
            problem_config[arg_name] = arg

        return {**problem_config, **kwargs}

    def set_problem(self, *args, **kwargs):
        self.set_start_state(*args, **kwargs)
        self.htn_model = self.create_htn_model(self.start_state)
        self.htn_model.scaffold = self.scaffold
        self.state = self.start_state

        self.problem_config = self._standardize_config(*args, **kwargs)
    
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
    
    def apply(self, action, reward=1):
        """ Applies an Action. Modifying self.state. """
        if (self.sai_makes_done(action.sai)):
            self.state = ProblemState({}, is_done=True)
        else:
            self.state = make_next_state(self.state, action.sai, reward)
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


    
