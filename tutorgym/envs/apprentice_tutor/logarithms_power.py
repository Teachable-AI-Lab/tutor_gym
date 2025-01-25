from random import randint
from random import choice
from pprint import pprint
import logging, operator
from functools import reduce

import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
from tutorgym.utils import OnlineDictVectorizer
import numpy as np
from colorama import Back, Fore

from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor, HTNCognitiveModel

import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re
from shop2.domain import Task, Operator, Method
from shop2.fact import Fact
from shop2.common import V



def apply_power_rule(init_value):
    a, p, b = re.findall(r'log\((\d+)\*\*(\d+),\s*(\d+)\)', str(parse_latex(init_value)))[0]
    answer = re.compile(rf"({p}\*log\({a}, {b}\)|log\({a}, {b}\)\*{p})")
    hint = rf"{p}*\log_{{{b}}}({{{a}}})"
    value = tuple([(answer, hint)])
    return hint

def solve_log(init_value):
    a, p, b = re.findall(r'log\((\d+)\*\*(\d+),\s*(\d+)\)', str(parse_latex(init_value)))[0]
    logba = sp.sympify(rf"log({a}, {b})")
    answer = re.compile(rf"({p}\*{logba}|{logba}\*{p})")
    hint = rf"{p}*{logba}"
    value = tuple([(answer, hint)])
    return hint

def simplify_exp(init_value):
    answer = re.compile(rf"{sp.simplify(parse_latex(init_value))}")
    hint = rf"{sp.simplify(parse_latex(init_value))}"
    value = tuple([(answer, hint)])
    return hint

Domain = {
    'done': Operator(head=('done',),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), answer=True)],
    ),

    'apply_power_rule': Operator(head=('apply_power_rule', V('equation')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=True)],
                                effects=[Fact(field='apply_power_rule', value=(apply_power_rule, V('eq')), how='ApplyPowerRule(a)', arg_foci='equation', answer=True)],
    ),

    'solve_log': Operator(head=('solve_log', V('equation')),
                        precondition=[Fact(field=V('equation'), value=V('eq'), answer=True)],
                        effects=[Fact(field='solve_log', value=(solve_log, V('eq')), how='SolveLog(a)', arg_foci='apply_power_rule', answer=True)],
    ),

    'simplify_exp': Operator(head=('simplify_exp', V('equation')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=True)],
                            effects=[Fact(field='simplify_exp', value=(simplify_exp, V('eq')), how='SimplifyExpression(a)', arg_foci='solve_log', answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(field=V('equation'), value=V('eq'), answer=True),
                    ],
                    subtasks=[
                        [
                            Task(head=('apply_power_rule', V('equation')), primitive=True),
                            Task(head=('solve_log', V('equation')), primitive=True),
                            Task(head=('simplify_exp', V('equation')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('apply_power_rule', V('equation')), primitive=True),
                            Task(head=('simplify_exp', V('equation')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_exp', V('equation')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ]
                    ]
    ),
}

class LogarithmsPower(ApprenticeTutor):
    def __init__(self, problem_types=["power"], **kwargs):
        """
        Creates a state and sets a random problem.
        """
        super().__init__(**kwargs)
        self.problem_types = problem_types
        self.set_random_problem()

    def _blank_state(self, type):
        field_params = {'x': 0, 'type': 'TextField', 'value' : "", 'width' : 100, 'height' : 50,  }
        button_params = {'x': 0, 'type': 'Button', 'width' : 100, 'height' : 50, }

        state: dict = {
            'equation' : {'y': 10, 'locked': True,  **field_params},
            'apply_power_rule' : {'y': 110, 'locked': False,  **field_params},
            'solve_log' : {'y': 210, 'locked': False, **field_params},
            'simplify_exp' : {'y': 310, 'locked': False, **field_params},
            'done' : {'y': 410, **button_params},
        }

        for key, value in state.items():
            state[key]['id'] = key

        self.possible_selections = ['apply_power_rule', 'solve_log', 'simplify_exp', 'done']
        self.possible_args = ['equation', 'apply_power_rule', 'solve_log']

        return ProblemState(state)                

    def set_start_state(self, *args, **kwargs):
        ''' Domain implementation: Used by ApprenticeTutor.set_problem() 
            to initialize a start state.'''
        state = self._blank_state(self.problem_types)

        # print("PROBLEM STATE", *args)
        self.problem = args[0]
        state['equation']['value'] = self.problem
        self.start_state = ProblemState(state)
    
    def set_random_problem(self):
        ptype: str = choice(self.problem_types)
        
        equation: str = ''
        if (ptype == "power"):
            b, a = choice([(base, base**power) for power in range(1, 10) for base in range(2, 32) if base**power <= 1024])
            p = randint(0, 20)
            p, b, a = 4,6, 216 
            equation = f"\\log_{{{b}}}{{{a}}}^{{{p}}}"

        self.set_problem(equation)

    def create_htn_model(self, state):
        curr_state = state.copy()
        task = [Task(head=('solve','equation'), primitive=False)]
        return HTNCognitiveModel(curr_state, task, Domain)
    
    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args

