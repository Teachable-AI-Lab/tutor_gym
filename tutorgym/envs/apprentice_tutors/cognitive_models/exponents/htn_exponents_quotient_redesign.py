import sympy as sp
from random import randint, choice

import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
from sympy import latex, sstr
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


def htn_exponents_quotient_problem():
    constant = randint(2,1000)
    exponent_1 = randint(10,20)
    exponent_2 = randint(2,9)
    return f"\\frac{{{constant}^{{{exponent_1}}}}}{{{constant}^{{{exponent_2}}}}}"

def rewrite_using_rule(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1].args[0].args[1]
    answer = sp.Pow(base, sp.Add(exp1, sp.Mul(-1, exp2), evaluate=False), evaluate=False)
    #answer = parse_latex(f"{base}^{{{exp1} - {exp2}}}")
    hint = f"{base}^{{{exp1} - {exp2}}}"
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex"))) 
    value = tuple([(answer, hint)])
    return value

def subtract_exponents(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1].args[0].args[1]
    answer = re.compile(rf"{exp1-exp2}")
    hint = rf"{{{exp1-exp2}}}"
    value = tuple([(answer, hint)])
    return value

def solve_using_quotient_rule(init_value):
    forumla = parse_latex(init_value)
    base = forumla.args[0].args[0]
    exp1 = forumla.args[0].args[1]
    exp2 = forumla.args[1].args[0].args[1]
    answer = sp.Pow(base, sp.Add(exp1, -exp2, evaluate=True), evaluate=False)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex"))) 
    value = tuple([(answer, hint)])
    return value


Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'rewrite_using_rule': Operator(head=('rewrite_using_rule', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='rewrite_using_rule', value=(rewrite_using_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'subtract_exponents': Operator(head=('subtract_exponents', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='subtract_exponents', value=(subtract_exponents, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve_using_quotient_rule': Operator(head=('solve_using_quotient_rule', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='solve_using_quotient_rule', value=(solve_using_quotient_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'apply_the_quotient_rule': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(field=V('equation'), value=V('eq'), answer=False),
                    ],
                    subtasks=[
                        (
                            Task(head=('rewrite_using_rule', V('equation'), ('rewrite_using_rule',)), primitive=True),
                            Task(head=('subtract_exponents', V('equation'), ('subtract_exponents',)), primitive=True),
                        ),
                    ]
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            (
                                Task(head=('apply_the_quotient_rule', V('equation')), primitive=False),
                                Task(head=('solve_using_quotient_rule', V('equation'), ('solve_using_quotient_rule',)), primitive=True),
                            ),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('solve_using_quotient_rule', V('equation'), ('solve_using_quotient_rule',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_exponents_quotient_kc_mapping():
    kcs = {
        "rewrite_using_rule": "rewrite_using_rule",
        "subtract_exponents": "subtract_exponents",
        "solve_using_quotient_rule": "solve_using_quotient_rule",
        "done": "done"
    }
    return kcs


def htn_exponents_quotient_intermediate_hints():
    hints = {
        "rewrite_using_rule": ["Rewrite using the quotient rule to subtract the exponents."],
        "subtract_exponents": ["Find the difference of the exponents."], 
        "solve_using_quotient_rule": ["Simplify the expression using the quotient rule.", "The quotient rule says that when you have a quotient or division of two exponential terms with the same base, you subtract the exponent of the denominator from the exponent of the numerator."],
        'done': [" You have solved the problem. Click the done button!"]
    }
    return hints

def htn_exponents_quotient_studymaterial():
    study_material = studymaterial["exponents_quotient_rule"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_exponents_redesign',
                                             'htn_exponents_quotient_redesign',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_exponents_quotient_problem,
                                             htn_exponents_quotient_kc_mapping(),
                                             htn_exponents_quotient_intermediate_hints(),
                                             htn_exponents_quotient_studymaterial()))