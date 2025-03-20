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


def htn_exponential_equations_different_base_problem():
    x = symbols('x')
    base_1 , base_2 = randint(2, 10), randint(2, 10)
    b = randint(-10, 10)
    while sp.Abs(b) <= 1 or base_1==base_2:
        base_1 , base_2 = randint(2, 10), randint(2, 10)
        b = randint(-10, 10)

    
    equation = latex(Eq(base_1**(x+b), base_2**x, evaluate=False)) ## not using a because math-field interprets a*x*log(base_1) as alog(base_1)
    return equation


def ln_both_sides(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    equation = Eq(sp.log(lhs, sp.E, evaluate=False), sp.ln(rhs, sp.E, evaluate=False), evaluate=False)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
    hint = latex(equation).replace('\log', '\ln')
    value = tuple([(answer, hint)])
    return value

def apply_logarithms_power_rule(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    lhs = lhs.as_base_exp()[1]*sp.ln(lhs.as_base_exp()[0])
    rhs = rhs.as_base_exp()[1]*sp.ln(rhs.as_base_exp()[0])
    equation = Eq(lhs, rhs, evaluate=False)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(equation).replace('\log', '\ln')
    value = tuple([(answer, hint)])
    return value

def distributive_property(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    lhs = lhs.as_base_exp()[1]*sp.ln(lhs.as_base_exp()[0])
    rhs = rhs.as_base_exp()[1]*sp.ln(rhs.as_base_exp()[0])
    equation = Eq(lhs.args[0].args[0]*lhs.args[1] + lhs.args[0].args[1]*lhs.args[1], rhs)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(equation).replace('\log', '\ln')
    value = tuple([(answer, hint)])
    return value

def group_for_x(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    lhs = lhs.as_base_exp()[1]*sp.ln(lhs.as_base_exp()[0])
    rhs = rhs.as_base_exp()[1]*sp.ln(rhs.as_base_exp()[0])
    equation = Eq(lhs.args[0].args[0]*(lhs.args[1]-rhs.args[1]), -lhs.args[0].args[1]*lhs.args[1])
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex").replace("x*(", "x("))))
    hint = latex(equation).replace('\log', '\ln')
    value = tuple([(answer, hint)])
    return value

def properties_of_logarithms(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    lhs = lhs.as_base_exp()[1]*sp.ln(lhs.as_base_exp()[0])
    rhs = rhs.as_base_exp()[1]*sp.ln(rhs.as_base_exp()[0])
    lhs_new = lhs.args[0].args[0]*sp.simplify((lhs.args[1]-rhs.args[1]))
    rhs_new = sp.Abs(lhs.args[0].args[1])*sp.ln(sp.Pow(sp.E**lhs.args[1], sp.sign(-lhs.args[0].args[1])), evaluate=False)
    equation = Eq(lhs_new, rhs_new)
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', re.sub(r'log\(([^)]+)\)', r'log(\1, E)', sstr(equation, order="grlex"))))
    hint = latex(equation).replace('\log', '\ln')
    value = tuple([(answer, hint)])
    return value

def solve_for_x(init_value):
    x = symbols('x')
    lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
    lhs = lhs.as_base_exp()[1]*sp.ln(lhs.as_base_exp()[0])
    rhs = rhs.as_base_exp()[1]*sp.ln(rhs.as_base_exp()[0])
    lhs_new = lhs.args[0].args[0]*sp.simplify((lhs.args[1]-rhs.args[1]))
    rhs_new = sp.Abs(lhs.args[0].args[1])*sp.ln(sp.Pow(sp.E**lhs.args[1], sp.sign(-lhs.args[0].args[1])), evaluate=False)
    equation = latex(Eq(lhs_new, rhs_new))
    equation = parse_latex(equation)
    
    solution = f"({equation.rhs.args[0]}*{equation.rhs.args[1]})/{equation.lhs.args[1]}"
    answer_1 = re.compile(re.sub(r'([-+^()*])', r'\\\1', solution))
    solution = f"{equation.rhs.args[0]}*({equation.rhs.args[1]}/{equation.lhs.args[1]})"
    answer_2 = re.compile(re.sub(r'([-+^()*])', r'\\\1', solution))
    solution = f"({equation.rhs.args[1]}/{equation.lhs.args[1]})*{equation.rhs.args[0]}"
    answer_3 = re.compile(re.sub(r'([-+^()*])', r'\\\1', solution))
    hint = latex((equation.rhs.args[0]*equation.rhs.args[1])/equation.lhs.args[1]).replace('\log', '\ln')
    value = tuple([
        (answer_1, hint),
        (answer_2, hint),
        (answer_3, hint)
    ])
    return value


Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),
    'ln_both_sides': Operator(head=('ln_both_sides', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='ln_both_sides', value=(ln_both_sides, V('eq')), kc=V('kc'), answer=True)]
    ),

    'apply_logarithms_power_rule': Operator(head=('apply_logarithms_power_rule', V('equation'), V('kc')),
                                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                            effects=[Fact(field='apply_logarithms_power_rule', value=(apply_logarithms_power_rule, V('eq')), kc=V('kc'), answer=True)]
    ),

    'distributive_property': Operator(head=('distributive_property', V('equation'), V('kc')),
                                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                        effects=[Fact(field='distributive_property', value=(distributive_property, V('eq')), kc=V('kc'), answer=True)]
    ),

    'group_for_x': Operator(head=('group_for_x', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='group_for_x', value=(group_for_x, V('eq')), kc=V('kc'), answer=True)]
    ),

    'properties_of_logarithms': Operator(head=('properties_of_logarithms', V('equation'), V('kc')),
                                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                        effects=[Fact(field='properties_of_logarithms', value=(properties_of_logarithms, V('eq')), kc=V('kc'), answer=True)]
    ),

    'solve_for_x': Operator(head=('solve_for_x', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='solve_for_x', value=(solve_for_x, V('eq')), kc=V('kc'), answer=True)]
    ),
    
    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_5'),
                        Fact(scaffold='level_4'),
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('apply_logarithms_power_rule', V('equation'), ('apply_logarithms_power_rule',)), primitive=True),
                            Task(head=('distributive_property', V('equation'), ('distributive_property',)), primitive=True),
                            Task(head=('group_for_x', V('equation'), ('group_for_x',)), primitive=True),
                            Task(head=('properties_of_logarithms', V('equation'), ('properties_of_logarithms',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('apply_logarithms_power_rule', V('equation'), ('apply_logarithms_power_rule',)), primitive=True),
                            Task(head=('distributive_property', V('equation'), ('distributive_property',)), primitive=True),
                            Task(head=('group_for_x', V('equation'), ('group_for_x',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('apply_logarithms_power_rule', V('equation'), ('apply_logarithms_power_rule',)), primitive=True),
                            Task(head=('distributive_property', V('equation'), ('distributive_property',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
                            Task(head=('apply_logarithms_power_rule', V('equation'), ('apply_logarithms_power_rule',)), primitive=True),
                            Task(head=('solve_for_x', V('equation'), ('solve_for_x',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('ln_both_sides', V('equation'), ('ln_both_sides',)), primitive=True),
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
