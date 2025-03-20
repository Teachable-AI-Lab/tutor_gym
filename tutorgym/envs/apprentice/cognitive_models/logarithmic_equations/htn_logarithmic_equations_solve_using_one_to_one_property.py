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


def htn_logarithmic_equations_solve_using_one_to_one_property_problem():
    x = symbols('x')
    x1, x2 = randint(-10, 10), randint(-10, 10)
    while not (x1+x2) or not (x1*x2):
      x1, x2 = randint(-10, 10), randint(-10, 10)
    equation = latex(Eq(sp.ln(x**2),sp.ln(-(x1+x2)*x -(x1*x2)), evaluate=False))
    return equation

def ln_both_sides(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def rhs_zero(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def factorized_form(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
        equation = Eq(equation.lhs-equation.rhs, 0)
        equation = sp.factor(equation)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def first_equation(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
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
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
        equation = Eq(equation.lhs-equation.rhs, 0)
        equation = sp.factor(equation)
        first = parse_latex(factor_eq).lhs
        second = sp.div(equation.lhs, first)[0]
        equation = Eq(second, 0)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def first_root(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
        equation = Eq(equation.lhs-equation.rhs, 0)
        equation = sp.factor(equation)
        if equation.lhs.args[1] == 2:
            equation = -equation.lhs.args[0].args[0]
            
            answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
            hint = latex(equation)
            value = tuple([(answer, hint)])

        else: 
            facts = list()
            for factor in equation.lhs.args:
                equation = -factor.args[0]
                answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
                hint = latex(equation)
                facts.append((answer, hint))
            value = tuple(facts)
        return value

def second_root(init_value, factor_eq):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.E**lhs, sp.E**rhs, evaluate=False)
        equation = parse_latex(latex(Eq(equation.lhs-equation.rhs, 0)))
        equation = Eq(equation.lhs-equation.rhs, 0)
        equation = sp.factor(equation)
        factor_eq = factor_eq
        first = x-parse_latex(factor_eq)
        second = sp.div(equation.lhs, first)[0]
        equation = -second.args[0]
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'ln_both_sides': Operator(head=('ln_both_sides', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='ln_both_sides', value=(ln_both_sides, V('eq')), kc=V('kc'), answer=True)],
    ),

    'rhs_zero': Operator(head=('rhs_zero', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='rhs_zero', value=(rhs_zero, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factorized_form': Operator(head=('factorized_form', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='factorized_form', value=(factorized_form, V('eq')), kc=V('kc'), answer=True)],
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

    'first_root': Operator(head=('first_root', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='first_root', value=(first_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_root': Operator(head=('second_root', V('equation'), V('factor'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                         Fact(field=V('factor'), value=V('factor_eq'), kc=V('fkc'), answer=True),
                            effects=[Fact(field='second_root', value=(second_root, V('eq'), V('factor_eq')), kc=V('kc'), answer=True)],
    ),


    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_4'),
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('rhs_zero', V('equation'), ('rhs_zero',)), primitive=True),
                            Task(head=('factorized_form', V('equation'), ('factorized_form',)), primitive=True),
                            Task(head=('first_equation', V('equation'), ('first_equation',)), primitive=True),
                            Task(head=('second_equation', V('equation'), 'first_equation', ('second_equation',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('rhs_zero', V('equation'), ('rhs_zero',)), primitive=True),
                            Task(head=('factorized_form', V('equation'), ('factorized_form',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('rhs_zero', V('equation'), ('rhs_zero',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ]
                    ]
    ),
}