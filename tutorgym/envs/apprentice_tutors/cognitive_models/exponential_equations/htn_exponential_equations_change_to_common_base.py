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


def htn_exponential_equations_change_to_common_base_problem():
    x = symbols('x')
    lhs_base, base = choice([(base**power, base) for power in range(1, 8) for base in range(2, 11) if base**power <= 512])
    rhs_base = choice([base**i for i in range(1, 10) if base**i <= 1024 and base**i!=lhs_base])

    a, b, c, d = randint(-10, 10), randint(-10, 10), randint(-10, 10), randint(-10, 10)
    while not (a*c) or (a==c):
        a, c = randint(-10, 10), randint(-10, 10)
    equation = latex(Eq(lhs_base**(a*x+b), rhs_base**(c*x+d), evaluate=False))
    return equation

def change_to_common_base(init_value):
        facts = list()
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs.as_base_exp(), parse_latex(init_value).rhs.as_base_exp()
        for base in range(2, 11):
            if sp.log(lhs[0], base).is_integer and sp.log(rhs[0], base).is_integer:
                lhs_base = sp.Pow(base, sp.log(lhs[0], base), evaluate=False)
                rhs_base = sp.Pow(base, sp.log(rhs[0], base), evaluate=False)
                equation = Eq(sp.Pow(lhs_base, lhs[1], evaluate=False), sp.Pow(rhs_base, rhs[1], evaluate=False), evaluate=False)
                answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
                hint = latex(equation)
                facts.append((answer, hint))
        value = tuple(facts)
        return value

def apply_exponents_power_rule(init_value):
        x = symbols('x')
        lhs, rhs = parse_latex(init_value).lhs, parse_latex(init_value).rhs
        equation = Eq(sp.simplify(lhs), sp.simplify(rhs), evaluate=False)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def apply_one_to_one_property(init_value):
        x = symbols('x')
        exponential_equation = sp.simplify(parse_latex(init_value))
        lhs, rhs = exponential_equation.lhs, exponential_equation.rhs
        equation = Eq(lhs.as_base_exp()[1], rhs.as_base_exp()[1], evaluate=False)
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(equation, order="grlex")))
        hint = latex(equation)
        value = tuple([(answer, hint)])
        return value

def solve_linear_equation(init_value):
        x = symbols('x')
        exponential_equation = sp.simplify(parse_latex(init_value))
        lhs, rhs = exponential_equation.lhs, exponential_equation.rhs
        linear_equation = Eq(lhs.as_base_exp()[1], rhs.as_base_exp()[1], evaluate=False)
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

    'change_to_common_base': Operator(head=('change_to_common_base', V('equation'), V('kc')),
                                      precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                      effects=[Fact(field='change_to_common_base', value=(change_to_common_base, V('eq')), kc=V('kc'), answer=True)]
    ),

    'apply_exponents_power_rule': Operator(head=('apply_exponents_power_rule', V('equation'), V('kc')),
                                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                           effects=[Fact(field='apply_exponents_power_rule', value=(apply_exponents_power_rule, V('eq')), kc=V('kc'), answer=True)]
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
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                         [
                           Task(head=('change_to_common_base', V('equation'), ('change_to_common_base',)), primitive=True),
                           Task(head=('apply_exponents_power_rule', V('equation'), ('apply_exponents_power_rule',)), primitive=True),
                           Task(head=('apply_one_to_one_property', V('equation'), ('apply_one_to_one_property',)), primitive=True),
                           Task(head=('solve_linear_equation', V('equation'), ('solve_linear_equation',)), primitive=True),
                           Task(head=('done', ('done',)), primitive=True)
                        ],

                         [
                           Task(head=('change_to_common_base', V('equation'), ('change_to_common_base',)), primitive=True),
                           Task(head=('apply_exponents_power_rule', V('equation'), ('apply_exponents_power_rule',)), primitive=True),
                           Task(head=('solve_linear_equation', V('equation'), ('solve_linear_equation',)), primitive=True),
                           Task(head=('done', ('done',)), primitive=True)
                        ],

                         [
                           Task(head=('change_to_common_base', V('equation'), ('change_to_common_base',)), primitive=True),
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

def htn_exponential_equations_change_to_common_base_kc_mapping():
    kcs = {
        "change_to_common_base": "change_to_common_base",
        "apply_exponents_power_rule": "apply_exponents_power_rule",
        "apply_one_to_one_property": "apply_one_to_one_property",
        "solve_linear_equation": "solve_linear_equation",
        "done": "done"
    }
    return kcs


def htn_exponential_equations_change_to_common_base_intermediate_hints():
    hints = {
        "change_to_common_base": ["Change the exponential equation to a common base."],
        "apply_exponents_power_rule": ["Apply the power rule for exponents"],
        "apply_one_to_one_property": ["Apply the one-to-one property for exponents."],
        "solve_linear_equation": ["Solve the linear equation for \(x\)."], 
    }
    return hints

def htn_exponential_equations_change_to_common_base_studymaterial():
    study_material = studymaterial["exponential_equations_change_to_common_base"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_exponential_equations',
                                             'htn_exponential_equations_change_to_common_base',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_exponential_equations_change_to_common_base_problem,
                                             htn_exponential_equations_change_to_common_base_kc_mapping(),
                                             htn_exponential_equations_change_to_common_base_intermediate_hints(),
                                             htn_exponential_equations_change_to_common_base_studymaterial()))