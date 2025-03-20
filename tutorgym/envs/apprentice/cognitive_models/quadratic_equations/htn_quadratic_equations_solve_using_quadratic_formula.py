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
    
def htn_quadratic_equations_solve_using_quadratic_formula_problem():
    x = sp.symbols('x')
    a, b, c = 0, 0, 0
    while not (a*b*c) or (b**2 - 4*a*c) < 0:
       a, b, c = randint(-5, 5), randint(-10, 10), randint(-5, 5)
    equation = latex(sp.Eq(a*x**2+b*x+c, 0))
    return equation

def d_value(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    d = b**2 - 4*a*c
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(d, order="grlex")))
    hint = latex(d)
    return tuple([(answer, hint)])

def sqrt_d_value(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    root_d = sp.sqrt(b**2 - 4*a*c)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root_d, order="grlex")))
    hint = latex(root_d)
    return tuple([(answer, hint)])

def first_numerator(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    numerator = -b + sp.sqrt(b**2 - 4*a*c)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(numerator, order="grlex")))
    hint = latex(numerator)
    return tuple([(answer, hint)])

def second_numerator(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    numerator = -b - sp.sqrt(b**2 - 4*a*c)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(numerator, order="grlex")))
    hint = latex(numerator)
    return tuple([(answer, hint)])

def denominator(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    denominator = 2 * init_equation.coeff(x, 2)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(denominator, order="grlex")))
    hint = latex(denominator)
    return tuple([(answer, hint)])


def first_root(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    numerator = -b + sp.sqrt(b**2 - 4*a*c)
    denominator = 2 * a
    root = sp.expand(numerator/denominator)
    answer = sp.sstr(root, order="grlex")
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
    hint = latex(root)
    return tuple([(answer, hint)])

def second_root(init_value):
    x = symbols('x')
    init_equation = sp.simplify(parse_latex(init_value).lhs)
    a, b, c = init_equation.coeff(x, 2), init_equation.coeff(x, 1), init_equation.coeff(x, 0)
    numerator = -b - sp.sqrt(b**2 - 4*a*c)
    denominator = 2 * a
    root = sp.expand(numerator/denominator)
    answer = sp.sstr(root, order="grlex")
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
    hint = latex(root)
    return tuple([(answer, hint)])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'd_value': Operator(head=('d_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='d_value', value=(d_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'sqrt_d_value': Operator(head=('sqrt_d_value', V('equation'), V('d'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='sqrt_d_value', value=(sqrt_d_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'first_numerator': Operator(head=('first_numerator', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='first_numerator', value=(first_numerator, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_numerator': Operator(head=('second_numerator', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='second_numerator', value=(second_numerator, V('eq')), kc=V('kc'), answer=True)],
    ),

    'denominator': Operator(head=('denominator', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='denominator', value=(denominator, V('eq')), kc=V('kc'), answer=True)],
    ),

    'first_root': Operator(head=('first_root', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='first_root', value=(first_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_root': Operator(head=('second_root', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='second_root', value=(second_root, V('eq')), kc=V('kc'), answer=True)],
    ),  

    
    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('d_value', V('equation'), ('d_value',)), primitive=True),
                            Task(head=('sqrt_d_value', V('equation'), 'd_value', ('sqrt_d_value',)), primitive=True),
                            Task(head=('first_numerator', V('equation'), ('first_numerator',)), primitive=True),
                            Task(head=('second_numerator', V('equation'), ('second_numerator',)), primitive=True),
                            Task(head=('denominator', V('equation'), ('denominator',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('d_value', V('equation'), ('d_value',)), primitive=True),
                            Task(head=('sqrt_d_value', V('equation'), 'd_value', ('sqrt_d_value',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}