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


def htn_exponents_power_problem():
    constant = randint(2,1000)
    exponent_1 = randint(2,12)
    exponent_2 = randint(2,12)
    return f"({constant}^{{{exponent_1}}})^{{{exponent_2}}}"
    # return  "(" + str(constant) + "^" + "{" + str(exponent_1) + "})"+ "^" + "{" + str(exponent_2) + "}"


def multiply_values(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1]
    answer = re.compile(rf"{base}\*\*\(({exp1}\*{exp2})|({exp2}\*{exp1})\)")  
    hint = rf"{base}^{{{exp1} \cdot {exp2}}}"  
    value = tuple([(answer, hint)])
    return value

def simplify_exp(init_value):
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

    'multiply_values': Operator(head=('multiply_values', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='multiply_values', value=(multiply_values, V('eq')), kc=V('kc'), answer=True)],
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
                            Task(head=('multiply_values', V('equation'), ('multiply_values',)), primitive=True),
                            Task(head=('simplify_exp', V('equation'), ('simplify_exp',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_exp', V('equation'), ('multiply_values', 'simplify_exp')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}
