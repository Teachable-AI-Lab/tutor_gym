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

def htn_quadratic_equations_nature_of_solution_problem():
    x = sp.symbols('x')
    a, b, c = 0, 0, 0
    while not b or not c or not a:
       a, b, c = randint(-10, 10), randint(-10, 10), randint(-10, 10)
    equation = latex(sp.Eq(a*x**2+b*x+c, 0))
    return equation

def squared_b_value(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = sp.simplify(init_equation.lhs).coeff(x, 1) 
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(b**2)))
    hint = latex(b**2)
    value = tuple([(answer, hint)])
    return value

def ac_product(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    ac = sp.simplify(init_equation.lhs).coeff(x, 2) * sp.simplify(init_equation.lhs).coeff(x, 0) 
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(4*ac)))
    hint = latex(4*ac)
    value = tuple([(answer, hint)])
    return value

def d_expression(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = sp.simplify(init_equation.lhs).coeff(x, 1) 
    ac = sp.simplify(init_equation.lhs).coeff(x, 2) * sp.simplify(init_equation.lhs).coeff(x, 0) 
    b_2 = b**2
    d = int(b_2) - 4*int(ac)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(d)))
    hint = latex(d)
    value = tuple([(answer, hint)])
    return value

def type_of_roots(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = sp.simplify(init_equation.lhs).coeff(x, 1) 
    ac = sp.simplify(init_equation.lhs).coeff(x, 2) * sp.simplify(init_equation.lhs).coeff(x, 0) 
    b_2 = b**2
    d = int(b_2) - 4*int(ac)
    if int(d) > 0:
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(parse_latex("realdistinct"), order="grlex")))
        return tuple([(answer, "real and distinct")])
    if int(d) == 0:
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(parse_latex("realequal"), order="grlex")))
        return tuple([(answer, "real and equal")])
    if int(d) < 0:
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(parse_latex("imaginary"), order="grlex")))
        return tuple([(answer, "imaginary")])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'squared_b_value': Operator(head=('squared_b_value', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='squared_b_value', value=(squared_b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'ac_product': Operator(head=('ac_product', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='ac_product', value=(ac_product, V('eq')), kc=V('kc'), answer=True)],
    ),

    'd_expression': Operator(head=('d_expression', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='d_expression', value=(d_expression, V('eq')), kc=V('kc'), answer=True)],
    ),

    'type_of_roots': Operator(head=('type_of_roots', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='type_of_roots', value=(type_of_roots, V('eq')), kc=V('kc'), answer=True)],
    ),


    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('squared_b_value', V('equation'), ('squared_b_value',)), primitive=True),
                            Task(head=('ac_product', V('equation'), ('ac_product',)), primitive=True),
                            Task(head=('d_expression', V('equation'), ('d_expression',)), primitive=True),
                            Task(head=('type_of_roots', V('equation'), ('type_of_roots',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('squared_b_value', V('equation'), ('squared_b_value',)), primitive=True),
                            Task(head=('ac_product', V('equation'), ('ac_product',)), primitive=True),
                            Task(head=('type_of_roots', V('equation'), ('type_of_roots',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('type_of_roots', V('equation'), ('type_of_roots',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}