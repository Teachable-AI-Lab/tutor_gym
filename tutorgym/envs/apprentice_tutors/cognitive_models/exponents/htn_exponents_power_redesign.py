import sympy as sp
from random import randint, choice

import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

from htn_cognitive_models import HTNCognitiveModel
from htn_cognitive_models import htn_loaded_models
from studymaterial import studymaterial


def htn_exponents_power_problem():
    constant = randint(2,1000)
    exponent_1 = randint(2,12)
    exponent_2 = randint(2,12)
    return f"({constant}^{{{exponent_1}}})^{{{exponent_2}}}"
    # return  "(" + str(constant) + "^" + "{" + str(exponent_1) + "})"+ "^" + "{" + str(exponent_2) + "}"


def rewrite_using_rule(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1]
    answer = re.compile(rf"{base}\*\*\(({exp1}\*{exp2})|({exp2}\*{exp1})\)")  
    hint = rf"{base}^{{{exp1} \cdot {exp2}}}"  
    value = tuple([(answer, hint)])
    return value

def multiply_exponents(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1]
    answer = re.compile(rf"{exp1*exp2}")
    hint = rf"{{{exp1*exp2}}}"
    value = tuple([(answer, hint)])
    return value

def solve_using_power_rule(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1]
    answer = re.compile(rf"{base}\*\*{exp1*exp2}")
    hint = rf"{base}^{{{exp1*exp2}}}"
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'rewrite_using_rule': Operator(head=('rewrite_using_rule', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='rewrite_using_rule', value=(rewrite_using_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'multiply_exponents': Operator(head=('multiply_exponents', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='multiply_exponents', value=(multiply_exponents, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve_using_power_rule': Operator(head=('solve_using_power_rule', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='solve_using_power_rule', value=(solve_using_power_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'apply_the_power_rule': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(field=V('equation'), value=V('eq'), answer=False),
                    ],
                    subtasks=[
                        (
                            Task(head=('rewrite_using_rule', V('equation'), ('rewrite_using_rule',)), primitive=True),
                            Task(head=('multiply_exponents', V('equation'), ('multiply_exponents',)), primitive=True),
                        ),
                    ]
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            (
                                Task(head=('apply_the_power_rule', V('equation')), primitive=False),
                                Task(head=('solve_using_power_rule', V('equation'), ('solve_using_power_rule',)), primitive=True),
                            ),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('solve_using_power_rule', V('equation'), ('solve_using_power_rule',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_exponents_power_kc_mapping():
    kcs = {
        "rewrite_using_rule": "rewrite_using_rule",
        "multiply_exponents": "multiply_exponents",
        "solve_using_power_rule": "solve_using_power_rule",
        "done": "done"
    }
    return kcs


def htn_exponents_power_intermediate_hints():
    hints = {
        "rewrite_using_rule": ["Rewrite using the power rule to perform multiplication with the exponents."],
        "multiply_exponents": ["Find the product of the exponents."], 
        "solve_using_power_rule": ["Simplify the expression using the power rule", "The power rule says that when you have a power to a power, you multiply the exponents."],
        'done': [" You have solved the problem. Click the done button!"]
    }
    return hints

def htn_exponents_power_studymaterial():
    study_material = studymaterial["exponents_power_rule"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_exponents_redesign',
                                             'htn_exponents_power_redesign',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_exponents_power_problem,
                                             htn_exponents_power_kc_mapping(),
                                             htn_exponents_power_intermediate_hints(),
                                             htn_exponents_power_studymaterial()))