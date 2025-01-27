import sympy as sp
from random import randint, choice

from sympy import sstr
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from shop2.domain import Task, Operator, Method
from shop2.fact import Fact
from shop2.common import V


def find_factors(x):
    factors = []
    for i in range(1, x + 1):
       if x % i == 0:
           factors.append(i)
    return factors

def htn_radicals_product_rule_problem():
    perfect_square = (randint(1,9)) ** 2
    factors_of_perfect_square = find_factors(perfect_square)
    random_factor_1 = choice(factors_of_perfect_square)
    random_factor_2 = int(perfect_square / random_factor_1)
    return f"\sqrt{{{random_factor_1}}} \cdot \sqrt{{{random_factor_2}}}"

def apply_product_rule(init_value):
    n, m = re.findall(r'\d+', init_value)
    answer = parse_latex(f"\\sqrt{{{n}*{m}}}")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    hint = f"\\sqrt{{{n}*{m}}}"
    return tuple([(answer, hint)])

def update_product_value(init_value):
    n, m = [int(x) for x in re.findall(r'\d+', init_value)]
    answer = parse_latex(f"\\sqrt{{{n*m}}}")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    hint = f"\\sqrt{{{n*m}}}"
    return tuple([(answer, hint)])

def simplify_product_value(init_value):
    n, m = [int(x) for x in re.findall(r'\d+', init_value)]
    answer = parse_latex(f"{sp.sqrt(n*m)}")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    hint = f"{sp.sqrt(n*m)}"
    return tuple([(answer, hint)])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'apply_product_rule': Operator(head=('apply_product_rule', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='apply_product_rule', value=(apply_product_rule, V('eq')), kc=V('kc'), answer=True)],
    ),
    'update_product_value': Operator(head=('update_product_value', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='update_product_value', value=(update_product_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'simplify_product_value': Operator(head=('simplify_product_value', V('equation'), V('kc')),
                                       precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                       effects=[Fact(field='simplify_product_value', value=(simplify_product_value, V('eq')), kc=V('kc'), answer=True)],
    ),


    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('apply_product_rule', V('equation'), ('apply_product_rule',)), primitive=True),
                            Task(head=('update_product_value', V('equation'), ('update_product_value',)), primitive=True),
                            Task(head=('simplify_product_value', V('equation'), ('simplify_product_value',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('apply_product_rule', V('equation'), ('apply_product_rule',)), primitive=True),
                            Task(head=('simplify_product_value', V('equation'), ('update_product_value','simplify_product_value',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_product_value', V('equation'), ('apply_product_rule','update_product_value','simplify_product_value',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ]
                    ]
    ),
}

