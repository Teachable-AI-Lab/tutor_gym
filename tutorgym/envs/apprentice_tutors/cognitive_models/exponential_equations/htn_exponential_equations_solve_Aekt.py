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


def htn_exponential_equations_solve_Aekt_problem():
    x = symbols('x')
    a, k = randint(1, 10), randint(-10, 10)
    c1, c2 = randint(-5, 10), randint(-5, 10)
    while (c2-c1) <= 0 or  sp.Abs(k) <= 1:
        c1, c2, k = randint(-10, 10), randint(-10, 10), randint(-10, 10)
    a, k, c1, c2 = 6,-6,4,9
    equation = latex(Eq(a*sp.E**(k*x)+c1, c2, evaluate=False))
    return equation

def coeff0_to_rhs(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    equation = Eq(lhs-lhs.coeff(x, 0), rhs-lhs.coeff(x,0))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

def coeffk_to_rhs(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    equation = Eq(lhs-lhs.coeff(x, 0), rhs-lhs.coeff(x,0))
    lhs, rhs = equation.lhs, equation.rhs
    coeffk = lhs.args[0]
    equation = Eq(lhs/coeffk, rhs/coeffk)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

def ln_both_sides(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    equation = Eq(lhs-lhs.coeff(x, 0), rhs-lhs.coeff(x,0))
    lhs, rhs = equation.lhs, equation.rhs
    coeffk = lhs.args[0]
    equation = Eq(lhs/coeffk, rhs/coeffk)
    lhs, rhs = equation.lhs, equation.rhs
    equation = Eq(lhs.args[1], sp.ln(rhs))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

def solve_for_x(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    equation = Eq(lhs-lhs.coeff(x, 0), rhs-lhs.coeff(x,0))
    lhs, rhs = equation.lhs, equation.rhs
    coeffk = lhs.args[0]
    equation = Eq(lhs/coeffk, rhs/coeffk)
    lhs, rhs = equation.lhs, equation.rhs
    equation = Eq(lhs.args[1], sp.ln(rhs))
    equation = parse_latex(latex(equation))
    lhs, rhs = equation.lhs, equation.rhs
    k = lhs.args[0]
    equation = rhs/k
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation)
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),
    'coeff0_to_rhs': Operator(head=('coeff0_to_rhs', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='coeff0_to_rhs', value=(coeff0_to_rhs, V('eq')), kc=V('kc'), answer=True)]
    ),

    'coeffk_to_rhs': Operator(head=('coeffk_to_rhs', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='coeffk_to_rhs', value=(coeffk_to_rhs, V('eq')), kc=V('kc'), answer=True)]
    ),

    'ln_both_sides': Operator(head=('ln_both_sides', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='ln_both_sides', value=(ln_both_sides, V('eq')), kc=V('kc'), answer=True)]
    ),

    'solve_for_x': Operator(head=('solve_for_x', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='solve_for_x', value=(solve_for_x, V('eq')), kc=V('kc'), answer=True)]
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('coeff0_to_rhs', V('equation'), ('coeff0_to_rhs',)), primitive=True),
                            Task(head=('coeffk_to_rhs', V('equation'), ('coeffk_to_rhs',)), primitive=True),
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('coeff0_to_rhs', V('equation'), ('coeff0_to_rhs',)), primitive=True),
                            Task(head=('coeffk_to_rhs', V('equation'), ('coeffk_to_rhs',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('coeff0_to_rhs', V('equation'), ('coeff0_to_rhs',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_exponential_equations_solve_Aekt_kc_mapping():
    kcs = {
        "coeff0_to_rhs": "coeff0_to_rhs",
        "coeffk_to_rhs": "coeffk_to_rhs",
        "ln_both_sides": "ln_both_sides",
        "solve_for_x": "solve_for_x",
        "done": "done"
    }
    return kcs

def htn_exponential_equations_solve_Aekt_intermediate_hints():
    hints = {
        "coeff0_to_rhs" : ["Move the constant term to the right-hand side of the equation."],
        "coeffk_to_rhs" : ["Move the coefficient of the exponential term to the right-hand side of the equation."],
        "ln_both_sides" : ["Take the natural log of both sides of the equation."],
        "solve_for_x" : ["Solve for x."],
    }
    return hints

def htn_exponential_equations_solve_Aekt_studymaterial():
    study_material = studymaterial["exponential_equations_solve_Aekt"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_exponential_equations',
                                             'htn_exponential_equations_solve_Aekt',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_exponential_equations_solve_Aekt_problem,
                                             htn_exponential_equations_solve_Aekt_kc_mapping(),
                                             htn_exponential_equations_solve_Aekt_intermediate_hints(),
                                             htn_exponential_equations_solve_Aekt_studymaterial()))