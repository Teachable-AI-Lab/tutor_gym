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

def root_to_exponent_form(expression):
    pattern = r"\\sqrt\[(\d+)\]\{(\d+)\^\{(\d+)\}\}"
    match = re.match(pattern, expression)
    if match:
        d = int(match.group(1))
        base = match.group(2)
        c = match.group(3)
        return "{}^{{\\frac{{{}}}{{{}}}}}".format(base, c, d)
    else:
        return "Invalid LaTeX expression"


def htn_exponential_equations_fractional_exponents_common_base_problem():
    x = symbols('x')
    base = randint(2, 10)
    a, b, c = randint(-10, 10), randint(-10, 10), randint(2, 10)
    d = randint(c+1,11)
    while not a:
        a = randint(-10, 10)
    return "{0}^{{{1}x+{2}}}=\sqrt[{{{3}}}]{{{0}^{{{4}}}}}".format(base, a, b, d, c).replace("+-", "-") #Unable to display sqrt(a) as a^(1/2), either becomes a^0.5 or automatically converts to sqrt(a)

def fractional_exponents(init_value):
    x = symbols('x')
    equation = parse_latex(init_value)
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    rhs_as_exp = root_to_exponent_form(latex(rhs))
    equation = Eq(lhs, parse_latex(rhs_as_exp), evaluate=False)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

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
    linear_equation = Eq(lhs.as_base_exp()[1], rhs.as_base_exp()[1], evaluate=False)
    # linear_equation = parse_latex(linear_equation)
    solution = solve(linear_equation, x)[0]
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(solution, order="grlex")))
    hint = latex(solution)
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'fractional_exponents': Operator(head=('fractional_exponents', V('equation'), V('kc')),
                                     precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                     effects=[Fact(field='fractional_exponents', value=(fractional_exponents, V('eq')), kc=V('kc'), answer=True)]
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
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('fractional_exponents', V('equation'), ('fractional_exponents',)), primitive=True),
                            Task(head=('apply_one_to_one_property', V('equation'), ('apply_one_to_one_property',)), primitive=True),
                            Task(head=('solve_linear_equation', V('equation'), ('solve_linear_equation',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('fractional_exponents', V('equation'), ('fractional_exponents',)), primitive=True),
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