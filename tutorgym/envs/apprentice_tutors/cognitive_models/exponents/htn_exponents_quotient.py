import sympy as sp
from random import randint, choice

import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from sympy import latex, sstr
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


def htn_exponents_quotient_problem():
    constant = randint(2,1000)
    exponent_1 = randint(10,20)
    exponent_2 = randint(2,9)
    return f"\\frac{{{constant}^{{{exponent_1}}}}}{{{constant}^{{{exponent_2}}}}}"


def subtract_values(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1].args[0].args[1]
    answer = sp.Pow(base, sp.Add(exp1, -exp2, evaluate=False), evaluate=False)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex"))) 
    value = tuple([(answer, hint)])
    return value

def simplify_exp(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1].args[0].args[1]
    answer = sp.Pow(base, sp.Add(exp1, -exp2, evaluate=True), evaluate=False)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex"))) 
    
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'subtract_values': Operator(head=('subtract_values', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='subtract_values', value=(subtract_values, V('eq')), kc=V('kc'), answer=True)],
    ),

    'simplify_exp': Operator(head=('simplify_exp', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='simplify_exp', value=(simplify_exp, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(field=V('equation'), value=V('eq'), answer=False),
                    ],
                    subtasks=[
                        [
                            Task(head=('subtract_values', V('equation'), ('subtract_values',)), primitive=True),
                            Task(head=('simplify_exp', V('equation'), ('simplify_exp',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_exp', V('equation'), ('subtract_values', 'simplify_exp')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_exponents_quotient_kc_mapping():
    kcs = {
        "subtract_values": "subtract_values",
        "simplify_exp": "simplify_exp",
        "done": "done"
    }
    return kcs


def htn_exponents_quotient_intermediate_hints():
    hints = {
        "subtract_values": ["Use the quotient rule to shift the exponent to multiplication with the exponents."],
        "simplify_exp": ["Solve the exponents."], 
        'done': [" You have solved the problem. Click the done button!"]
    }
    return hints

def htn_exponents_quotient_studymaterial():
    study_material = studymaterial["exponents_quotient_rule"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_exponents',
                                             'htn_exponents_quotient',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_exponents_quotient_problem,
                                             htn_exponents_quotient_kc_mapping(),
                                             htn_exponents_quotient_intermediate_hints(),
                                             htn_exponents_quotient_studymaterial()))