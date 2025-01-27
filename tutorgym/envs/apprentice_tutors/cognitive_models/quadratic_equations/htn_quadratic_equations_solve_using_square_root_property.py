import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

def htn_quadratic_equations_solve_using_square_root_property_problem():
    x = sp.symbols('x')
    c1, c2 = -1, -1
    while (c2-c1) <= 0:
        c1, c2 = randint(-10, 10), randint(-10, 10)
    a = randint(1, 10)**2
    equation = latex(sp.Eq(a*x**2+c1, c2))
    return equation

def coeff0_to_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    a, c1, c2 = init_equation.lhs.coeff(x, 2), init_equation.lhs.coeff(x, 0), init_equation.rhs.coeff(x, 0)
    equation = sp.Eq(a*x**2, sp.Add(c2, -c1, evaluate=False))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])


def update_coeff0_on_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    a, c1, c2 = init_equation.lhs.coeff(x, 2), init_equation.lhs.coeff(x, 0), init_equation.rhs.coeff(x, 0)
    equation = sp.Eq(a*x**2, sp.Add(c2, -c1))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def coeff2_to_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    a, c1, c2 = init_equation.lhs.coeff(x, 2), init_equation.lhs.coeff(x, 0), init_equation.rhs.coeff(x, 0)
    equation = sp.Eq(x**2, sp.Mul(sp.Add(c2, -c1)/a, evaluate=False))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex").replace("*(1", "")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def update_coeff2_on_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    a, c1, c2 = init_equation.lhs.coeff(x, 2), init_equation.lhs.coeff(x, 0), init_equation.rhs.coeff(x, 0)
    equation = sp.Eq(x**2, sp.simplify(sp.Mul(sp.Add(c2, -c1),1/a)))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def positive_root(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    root = sp.solve(init_equation, x)[1]
    answer =  sp.sstr(root, order="grlex").replace("*","")
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
    hint = latex(root)
    return tuple([(answer, hint)])

def negative_root(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    root = sp.solve(init_equation, x)[0]
    answer =  sp.sstr(root, order="grlex").replace("*","")
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
    hint = latex(root)
    return tuple([(answer, hint)])


Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),
    'coeff0_to_rhs': Operator(head=('coeff0_to_rhs', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='coeff0_to_rhs', value=(coeff0_to_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'update_coeff0_on_rhs': Operator(head=('update_coeff0_on_rhs', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='update_coeff0_on_rhs', value=(update_coeff0_on_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'coeff2_to_rhs': Operator(head=('coeff2_to_rhs', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='coeff2_to_rhs', value=(coeff2_to_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'update_coeff2_on_rhs': Operator(head=('update_coeff2_on_rhs', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='update_coeff2_on_rhs', value=(update_coeff2_on_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'positive_root': Operator(head=('positive_root', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='positive_root', value=(positive_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'negative_root': Operator(head=('negative_root', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='negative_root', value=(negative_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('coeff0_to_rhs', V('equation'), ('coeff0_to_rhs',)), primitive=True),
                            Task(head=('update_coeff0_on_rhs', V('equation'), ('update_coeff0_on_rhs',)), primitive=True),
                            Task(head=('coeff2_to_rhs', V('equation'), ('coeff2_to_rhs',)), primitive=True),
                            Task(head=('update_coeff2_on_rhs', V('equation'), ('update_coeff2_on_rhs',)), primitive=True),
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('coeff0_to_rhs', V('equation'), ('coeff0_to_rhs',)), primitive=True),
                            Task(head=('update_coeff0_on_rhs', V('equation'), ('update_coeff0_on_rhs',)), primitive=True),
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}