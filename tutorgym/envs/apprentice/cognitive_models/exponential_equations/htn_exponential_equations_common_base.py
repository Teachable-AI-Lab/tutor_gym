from random import randint, choice

import sympy as sp
from sympy import latex, symbols, expand, sstr, Eq, solve
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V


def htn_exponential_equations_common_base_problem():
    x = symbols('x')
    base = randint(2, 10)
    a, b, c, d = randint(-10, 10), randint(-10, 10), randint(-10, 10), randint(-10, 10)
    while not (a*c) or (a==c):
        a, c = randint(-10, 10), randint(-10, 10)
    equation = latex(Eq(base**(a*x+b), base**(c*x+d), evaluate=False))
    return equation

def apply_one_to_one_property(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(lhs.as_base_exp()[1], rhs.as_base_exp()[1], evaluate=False)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def solve_linear_equation(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(lhs.as_base_exp()[1], rhs.as_base_exp()[1], evaluate=False)
        solution = solve(equation, x)[0]
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(solution, order="grlex")))
        hint = latex(solution)
        value = tuple([(answer, hint)])
        return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'apply_one_to_one_property': Operator(head=('apply_one_to_one_property', V('equation'), V('kc')),
                                          precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                          effects=[Fact(field='apply_one_to_one_property', value=(apply_one_to_one_property, V('eq')), kc=V('kc'), answer=True)]
    ),

    'solve_linear_equation': Operator(head=('solve_linear_equation', V('equation'), V('kc')),
                                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                        effects=[Fact(field='solve_linear_equation', value=(solve_linear_equation, V('eq')), kc=V('kc'), answer=True)]
    ),
        
    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                         [
                           Task(head=('apply_one_to_one_property', V('equation'), ('apply_one_to_one_property',)), primitive=True),
                           Task(head=('solve_linear_equation', V('equation'), ('solve_linear_equation',)), primitive=True),
                           Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                           Task(head=('solve_linear_equation', V('equation'), ('solve_linear_equation',)), primitive=True),
                           Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}
