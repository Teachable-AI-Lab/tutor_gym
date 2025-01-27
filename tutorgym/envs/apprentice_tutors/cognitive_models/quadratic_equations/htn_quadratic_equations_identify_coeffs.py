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

from htn_cognitive_models import HTNCognitiveModel
from htn_cognitive_models import htn_loaded_models
from studymaterial import studymaterial


def htn_quadratic_equations_identify_coeffs_problem():
    x = sp.symbols('x')
    x1, x2, coeff = 0, 0, 0
    while not (x1*x2) or not coeff:
      x1, x2 = randint(-10, 10), randint(-10, 10)
      factorlist = [f for factor in sp.divisors(int(x1)) for f in (factor, -factor) if (f*x2+x1)]
      if factorlist: 
        coeff = choice(factorlist)
    equation = f"{latex(expand(((coeff*x)-x1) * (x-x2)))}=0"
    return equation

def a_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 2))
    return tuple([(re.compile(answer), answer)])

def b_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 1))
    return tuple([(re.compile(answer), answer)])

def c_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 0))
    return tuple([(re.compile(answer), answer)])

def ac_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 0) * equation.coeff(x, 2))
    return tuple([(re.compile(answer), answer)])

def b2_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 1)**2)
    return tuple([(re.compile(answer), answer)])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'a_value': Operator(head=('a_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='a_value', value=(a_value, V('eq')), kc=V('kc'), answer=True)],
    ),  

    'b_value': Operator(head=('b_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='b_value', value=(b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'c_value': Operator(head=('c_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='c_value', value=(c_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'b2_value': Operator(head=('b2_value', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='b2_value', value=(b2_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'ac_value': Operator(head=('ac_value', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='ac_value', value=(ac_value, V('eq')), kc=V('kc'), answer=True)],
    ),



    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('b2_value', V('equation'), ('b2_value',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('b2_value', V('equation'), ('b2_value',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_quadratic_equations_identify_coeffs_kc_mapping():
    kcs = {
        "a_value": "update_a_value",
        "b_value": "update_b_value",
        "c_value": "update_c_value",
        "b2_value": "update_b2_value",
        "ac_value": "update_ac_value",
        "done": "done"
        }
    return kcs


def htn_quadratic_equations_identify_coeffs_intermediate_hints():
    hints = {
        "a_value": ["Here \(a\) is coefficient of \(x^2\)."],
        "b_value": ["Here \(b\) is coefficient of \(x\)."],
        "c_value": ["Here \(c\) is coefficient of the constant term."],
        "b2_value": ["Here \(b^2\) is the square of the coefficient of \(x\)."],
        "ac_value": ["Here \(ac\) is the product of the coefficients of \(x^2\) and constant."],
    }
    return hints

def htn_quadratic_equations_identify_coeffs_studymaterial():
    study_material = studymaterial["quadratic_equations_identify_coeffs"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_quadratic_equations',
                                             'htn_quadratic_equations_identify_coeffs',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_quadratic_equations_identify_coeffs_problem,
                                             htn_quadratic_equations_identify_coeffs_kc_mapping(),
                                             htn_quadratic_equations_identify_coeffs_intermediate_hints(),
                                             htn_quadratic_equations_identify_coeffs_studymaterial()))