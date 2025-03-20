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

def htn_exponential_equations_solve_quadratic_form_problem():
    x = symbols('x')
    ex = sp.E**x
    x1, x2 = randint(1, 10), randint(1, 10)
    while not (x1+x2) or not (x1*x2):
      x1, x2 = randint(1, 10), randint(1, 10)
    expanded_equation = expand((ex - x1) * (ex - x2))
    equation = latex(Eq(ex**2+(expanded_equation.coeff(ex))*ex, -(expanded_equation.coeff(x, 0)), evaluate=False))
    return equation

def rhs_zero(init_value):
    x = symbols('x')
    equation = parse_latex(init_value)

    equation = parse_latex(latex(Eq((equation.lhs)-equation.rhs, 0)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

def factorized_form(init_value):
    x = symbols('x')
    equation = parse_latex(init_value)
    equation = Eq(equation.lhs-equation.rhs, 0)
    equation = sp.factor(equation)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value


def first_equation(init_value):
    x = symbols('x')
    equation = parse_latex(init_value)
    equation = Eq(equation.lhs-equation.rhs, 0)
    equation = sp.factor(equation)

    if equation.lhs.args[1] == 2:
        factor_eq = Eq(equation.lhs.args[0], 0)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(factor_eq, order="grlex")))
        hint = latex(factor_eq)
        value = tuple([(answer, hint)])

    else:
        facts = list()
        for factor in equation.lhs.args:
            factor_eq = Eq(factor, 0)
            answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(factor_eq, order="grlex")))
            hint = latex(factor_eq)
            facts.append((answer, hint))
        value = tuple(facts)
    return value


def second_equation(init_value, factor_eq):
    x = symbols('x')
    equation = parse_latex(init_value)
    equation = Eq(equation.lhs-equation.rhs, 0)
    equation = sp.factor(equation)
    first = parse_latex(factor_eq).lhs
    second = sp.div(equation.lhs, first)[0]
    equation = Eq(second, 0)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

def first_x(equation):
    x = symbols('x')
    lhs = parse_latex(equation).lhs
    root = Eq(lhs.args[0] , -lhs.args[1])
    equation  = sp.ln(root.rhs) if root.rhs >=0 else parse_latex("NA")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(sp.ln(root.rhs)).replace('\log', '\ln') if root.rhs >=0 else "NA"
    value = tuple([(answer, hint)])
    return value


def second_x(equation):
    x = symbols('x')
    lhs = parse_latex(equation).lhs
    root = Eq(lhs.args[0] , -lhs.args[1])
    equation  = sp.ln(root.rhs) if root.rhs >=0 else parse_latex("NA")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(sp.ln(root.rhs)).replace('\log', '\ln') if root.rhs >=0 else "NA"
    value = tuple([(answer, hint)])
    return value



Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'rhs_zero': Operator(head=('rhs_zero', V('equation'), V('kc')),
                         precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                         effects=[Fact(field='rhs_zero', value=(rhs_zero,V('eq')), kc=V('kc'), answer=True)]
    ),

    'factorized_form': Operator(head=('factorized_form', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='factorized_form', value=(factorized_form,V('eq')), kc=V('kc'), answer=True)]
    ),

    'first_equation': Operator(head=('first_equation', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='first_equation', value=(first_equation, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_equation': Operator(head=('second_equation', V('equation'), V('factor'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                             Fact(field=V('factor'), value=V('factor_eq'), kc=V('fkc'), answer=True),
                                effects=[Fact(field='second_equation', value=(second_equation, V('eq'), V('factor_eq')), kc=V('kc'), answer=True)],
    ),

    'first_x': Operator(head=('first_x', V('equation'), V('first_equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                            Fact(field=V('first_equation'), value=V('first_eq'), kc=V('fkc'), answer=True),
                            effects=[Fact(field='first_x', value=(first_x, V('first_eq')), kc=V('kc'), answer=True)],
    ),

    'second_x': Operator(head=('second_x', V('equation'), V('second_equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                         Fact(field=V('second_equation'), value=V('second_eq'), kc=V('fkc'), answer=True),
                            effects=[Fact(field='second_x', value=(second_x, V('second_eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('rhs_zero', V('equation'), ('rhs_zero',)), primitive=True),
                            Task(head=('factorized_form', V('equation'), ('factorized_form',)), primitive=True),
                            Task(head=('first_equation', V('equation'), ('first_equation',)), primitive=True),
                            Task(head=('second_equation', V('equation'), 'first_equation', ('second_equation',)), primitive=True),
                            Task(head=('first_x', V('equation'), 'first_equation', ('first_x',)), primitive=True),
                            Task(head=('second_x', V('equation'), 'second_equation', ('second_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('rhs_zero', V('equation'), ('rhs_zero',)), primitive=True),
                            Task(head=('first_equation', V('equation'), ('first_equation',)), primitive=True),
                            Task(head=('second_equation', V('equation'), 'first_equation', ('second_equation',)), primitive=True),
                            Task(head=('first_x', V('equation'), 'first_equation', ('first_x',)), primitive=True),
                            Task(head=('second_x', V('equation'), 'second_equation', ('second_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('first_equation', V('equation'), ('first_equation',)), primitive=True),
                            Task(head=('second_equation', V('equation'), 'first_equation', ('second_equation',)), primitive=True),
                            Task(head=('first_x', V('equation'), 'first_equation', ('first_x',)), primitive=True),
                            Task(head=('second_x', V('equation'), 'second_equation', ('second_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}