import sympy as sp
from random import randint, choice

from sympy import sstr, latex
import re

from shop2.domain import Task, Operator, Method
from shop2.fact import Fact
from shop2.common import V


def generate_prime(x,y):
    prime_list = []
    for n in range(x, y):
        isPrime = True

        for num in range(2, n):
            if n % num == 0:
                isPrime = False

        if isPrime:
            prime_list.append(n)

    prime_choice = choice(prime_list)
           
    return prime_choice

    
def htn_radicals_subtracting_square_roots_problem():
    c1 = generate_prime(2,10)
    ra =  generate_prime(2,10)
    rb = (randint(2,6))** 2
    c2 = generate_prime(2,10)
    return f"{c1}\sqrt{{{ra * rb}}} - {c2}\sqrt{{{ra}}}"

def factor_radicand(init_value):
    c1, rarb, c2, ra = re.findall(r'\d+', init_value)
    c1, rarb, c2, ra = int(c1), int(rarb), int(c2), int(ra)
    rb = rarb // ra
    answer = sp.Add(sp.Mul(c1, sp.sqrt(sp.Mul(ra, rb, evaluate=False), evaluate=False), evaluate=False), sp.Mul(-c2, sp.sqrt(ra)), evaluate=False)
    hint = latex(sp.Mul(c1, sp.sqrt(sp.Mul(ra, rb, evaluate=False), evaluate=False), evaluate=False)) + "" + latex(sp.Mul(-c2, sp.sqrt(ra)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    
    return tuple([(answer, hint)])

def product_rule(init_value):
    c1, rarb, c2, ra = re.findall(r'\d+', init_value)
    c1, rarb, c2, ra = int(c1), int(rarb), int(c2), int(ra)
    rb = rarb // ra
    answer = sp.Add(sp.Mul(c1, sp.Mul(sp.sqrt(ra), sp.sqrt(rb, evaluate=False), evaluate=False), evaluate=False), sp.Mul(-c2, sp.sqrt(ra)), evaluate=False)
    hint = latex(sp.Mul(c1, sp.Mul(sp.sqrt(ra), sp.sqrt(rb, evaluate=False), evaluate=False), evaluate=False)) + "" + latex(sp.Mul(-c2, sp.sqrt(ra)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def solve_square_root(init_value):
    c1, rarb, c2, ra = re.findall(r'\d+', init_value)
    c1, rarb, c2, ra = int(c1), int(rarb), int(c2), int(ra)
    rb = rarb // ra
    ans1 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {c1}*{sp.sqrt(rb)}*sqrt({ra})"))
    ans2 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + ({c1}*{sp.sqrt(rb)})*sqrt({ra})"))
    ans3 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {c1}*({sp.sqrt(rb)}*sqrt({ra}))"))

    ans4 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {sp.sqrt(rb)}*{c1}*sqrt({ra})"))
    ans5 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + ({sp.sqrt(rb)}*{c1})*sqrt({ra})"))
    ans6 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {sp.sqrt(rb)}*({c1}*sqrt({ra}))"))

    ans7 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {c1}*sqrt({ra})*{sp.sqrt(rb)}"))
    ans8 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + ({c1}*sqrt({ra}))*{sp.sqrt(rb)}"))
    ans9 = re.compile(re.sub(r'([-+^()*])', r'\\\1', rf"-{c2}*sqrt({ra}) + {c1}*(sqrt({ra})*{sp.sqrt(rb)})"))
    
    answer = sp.Add(sp.Mul(c1, sp.Mul(sp.sqrt(ra), sp.sqrt(rb), evaluate=False), evaluate=False), sp.Mul(-c2, sp.sqrt(ra)), evaluate=False)
    hint = latex(sp.Mul(c1, sp.Mul(sp.sqrt(ra), sp.sqrt(rb), evaluate=False), evaluate=False)) + "" + latex(sp.Mul(-c2, sp.sqrt(ra)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    return tuple([
        (ans1, hint),
        (ans2, hint),
        (ans3, hint),
        (ans4, hint),
        (ans5, hint),
        (ans6, hint),
        (ans7, hint),
        (ans8, hint),
        (ans9, hint)
        ])

def evaluate_coefficient(init_value):
    c1, rarb, c2, ra = re.findall(r'\d+', init_value)
    c1, rarb, c2, ra = int(c1), int(rarb), int(c2), int(ra)
    rb = rarb // ra
    answer = sp.Add(sp.Mul(c1*sp.sqrt(rb), sp.sqrt(ra), evaluate=False), sp.Mul(-c2, sp.sqrt(ra)), evaluate=False)
    hint = latex(sp.Mul(c1*sp.sqrt(rb), sp.sqrt(ra), evaluate=False)) + "" + latex(sp.Mul(-c2, sp.sqrt(ra)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def subtracting_square_root(init_value):
    c1, rarb, c2, ra = re.findall(r'\d+', init_value)
    c1, rarb, c2, ra = int(c1), int(rarb), -1*int(c2), int(ra)
    rb = rarb // ra
    c3 = sp.sqrt(rb)*c1
    c4 = c3+c2
    ans1 = re.compile(rf"{c4}\*sqrt\({ra}\)")
    ans2 = re.compile(rf"sqrt\({ra}\)\*{c4}")
    answer = sp.simplify(sp.Add(sp.Mul(c1, sp.sqrt(ra), sp.sqrt(rb)), sp.Mul(c2, sp.sqrt(ra))))
    hint = latex(answer)
    return tuple([
        (ans1, hint),
        (ans2, hint)
    ])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'factor_radicand': Operator(head=('factor_radicand', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='factor_radicand', value=(factor_radicand, V('eq')), kc=V('kc'), answer=True)],
    ),
    'product_rule': Operator(head=('product_rule', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='product_rule', value=(product_rule, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve_square_root': Operator(head=('solve_square_root', V('equation'), V('kc')),
                                  precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                  effects=[Fact(field='solve_square_root', value=(solve_square_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'evaluate_coefficient': Operator(head=('evaluate_coefficient', V('equation'), V('kc')),
                                     precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                     effects=[Fact(field='evaluate_coefficient', value=(evaluate_coefficient, V('eq')), kc=V('kc'), answer=True)],
    ),

    'subtracting_square_root': Operator(head=('subtracting_square_root', V('equation'), V('kc')),
                                   precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                   effects=[Fact(field='subtracting_square_root', value=(subtracting_square_root, V('eq')), kc=V('kc'), answer=True)],
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
                            Task(head=('factor_radicand', V('equation'), ('factor_radicand',)), primitive=True),
                            Task(head=('product_rule', V('equation'), ('product_rule',)), primitive=True),
                            Task(head=('solve_square_root', V('equation'), ('solve_square_root',)), primitive=True),
                            Task(head=('evaluate_coefficient', V('equation'), ('evaluate_coefficient',)), primitive=True),
                            Task(head=('subtracting_square_root', V('equation'), ('subtracting_square_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('factor_radicand', V('equation'), ('factor_radicand',)), primitive=True),
                            Task(head=('product_rule', V('equation'), ('product_rule',)), primitive=True),
                            Task(head=('solve_square_root', V('equation'), ('solve_square_root',)), primitive=True),
                            Task(head=('subtracting_square_root', V('equation'), ('subtracting_square_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('factor_radicand', V('equation'), ('factor_radicand',)), primitive=True),
                            Task(head=('product_rule', V('equation'), ('product_rule',)), primitive=True),
                            Task(head=('subtracting_square_root', V('equation'), ('subtracting_square_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('factor_radicand', V('equation'), ('factor_radicand',)), primitive=True),
                            Task(head=('subtracting_square_root', V('equation'), ('subtracting_square_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('subtracting_square_root', V('equation'), ('subtracting_square_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}