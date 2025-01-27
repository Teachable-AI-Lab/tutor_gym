import sympy as sp
from random import randint, choice

import re
from shop2.domain import Task, Operator, Method
from shop2.fact import Fact
from shop2.common import V
from sympy.parsing.latex._parse_latex_antlr import parse_latex


def htn_logarithms_power_problem():
    b, a = choice([(base, base**power) for power in range(1, 10) for base in range(2, 32) if base**power <= 1024])
    p = randint(0, 20)
    p, b, a = 4,6, 216 
    return f"\\log_{{{b}}}{{{a}}}^{{{p}}}"

def apply_power_rule(init_value):
    a, p, b = re.findall(r'log\((\d+)\*\*(\d+),\s*(\d+)\)', str(parse_latex(init_value)))[0]
    answer = re.compile(rf"({p}\*log\({a}, {b}\)|log\({a}, {b}\)\*{p})")
    hint = rf"{p}*\log_{{{b}}}({{{a}}})"
    value = tuple([(answer, hint)])
    return value

def solve_log(init_value):
    a, p, b = re.findall(r'log\((\d+)\*\*(\d+),\s*(\d+)\)', str(parse_latex(init_value)))[0]
    logba = sp.sympify(rf"log({a}, {b})")
    answer = re.compile(rf"({p}\*{logba}|{logba}\*{p})")
    hint = rf"{p}*{logba}"
    value = tuple([(answer, hint)])
    return value

def simplify_exp(init_value):
    answer = re.compile(rf"{sp.simplify(parse_latex(init_value))}")
    hint = rf"{sp.simplify(parse_latex(init_value))}"
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'apply_power_rule': Operator(head=('apply_power_rule', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='apply_power_rule', value=(apply_power_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve_log': Operator(head=('solve_log', V('equation'), V('kc')),
                        precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                        effects=[Fact(field='solve_log', value=(solve_log, V('eq')), kc=V('kc'), answer=True)],
    ),

    'simplify_exp': Operator(head=('simplify_exp', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='simplify_exp', value=(simplify_exp, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(field=V('equation'), value=V('eq'), answer=False),
                    ],
                    subtasks=[
                        [
                            Task(head=('apply_power_rule', V('equation'), ('apply_power_rule',)), primitive=True),
                            Task(head=('solve_log', V('equation'), ('solve_log',)), primitive=True),
                            Task(head=('simplify_exp', V('equation'), ('simplify_exp',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('apply_power_rule', V('equation'), ('apply_power_rule',)), primitive=True),
                            Task(head=('simplify_exp', V('equation'), ('solve_log', 'simplify_exp')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_exp', V('equation'), ('apply_power_rule', 'solve_log', 'simplify_exp')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ]
                    ]
    ),
}