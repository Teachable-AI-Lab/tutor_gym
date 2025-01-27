import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols, Eq, solve
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

import math
from random import random
from functools import reduce


def quadratic_factorization(expression):
    x = sp.symbols('x')

    # Convert the expression to SymPy format
    expression = expression.replace("^", "**")  # Replace "^" with "**" for exponentiation
    expression = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', expression)  # Add "*" for multiplication between coefficient and variable

    # Parse the expression and factor it
    factored_expression = sp.factor(expression)

    return str(factored_expression.args[0]).replace("*",""), str(factored_expression.args[1]).replace("*","")


def factors(n):
    fset = set(reduce(list.__add__,
                      ([i, n//i] for i in range(1, int(abs(n)**0.5) + 1)
                       if n % i == 0)))

    other_signs = set([-1 * f for f in fset])
    fset = fset.union(other_signs)

    return fset


def factor_grouping_problem():
    n1 = randint(2, 5)

    n2 = randint(1, 5)
    if random() > 0.5:
        n2 *= -1

    n3 = randint(1, 5)

    n4 = randint(1, 5)
    if random() > 0.5:
        n4 *= -1

    if math.gcd(n1, n2) != 1 or math.gcd(n3, n4) != 1:
        return factor_grouping_problem()

    problem = "{}x^2".format(n1*n3)

    b_value = n1*n4+n2*n3
    if b_value == 0:
        return factor_grouping_problem()

    if b_value > 0:
        problem += "+"

    problem += "{}x".format(b_value)

    c_value = n2 * n4
    if c_value > 0:
        problem += "+"

    problem += "{}".format(c_value)

    return problem


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

def factor_1_b(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)
    factors = [f for factor in sp.divisors(int(product_ac)) for f in (factor, -factor)]
    factorlist = [(abs((int(product_ac)/f+f)-int(sum_b)), f) for f in factors]
    factorlist.sort()
    value = tuple([(re.compile(str(f)), str(f)) for _, f in factorlist])
    return value

def factor_2_b(init_value, f1):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)
    answer = re.compile(str(int(int(product_ac)/int(f1))))
    hint = str(int(int(product_ac)/int(f1)))
    value = tuple([(answer, hint)])
    return value

def sum_factor(f1, f2):
    sum_factor = int(f1) + int(f2)
    value = tuple([(re.compile(str(sum_factor)), str(sum_factor))])
    return value

def sum_c(init_value, sum_factor):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    if sum_b == int(sum_factor):
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('checked')))), 'checked')])
    else:
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('unchecked')))), 'unchecked')])
    return value

def p_value(factor_1_b, factor_2_b):
    return tuple([
        (re.compile(factor_1_b), factor_1_b),
        (re.compile(factor_2_b), factor_2_b)
        ])

def q_value(factor_1_b, factor_2_b, p_value):
    if p_value == factor_1_b:
        return tuple([(re.compile(factor_2_b), factor_2_b)])
    return tuple([(re.compile(factor_1_b), factor_1_b)])

def first_part(init_value, p_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    a = equation.coeff(x, 2)
    p = int(p_value)
    answer = a*x**2 + p*x
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def second_part(init_value, q_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    c = equation.coeff(x, 0)
    q = int(q_value)
    answer = q*x + c
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def gcf_1_factor(first_part):
    x = symbols('x')
    first_part = parse_latex(first_part)
    answer = sp.factor(first_part)
    hint = latex(answer)
    if answer.args[1] == 2:
        answer = f"{answer.args[0]}"
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
        return tuple([(answer, hint)])
        
    elif len(answer.args) == 2:
        ans1 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{'*'.join(map(str, answer.args[:-1]))}({answer.args[-1]})"))
        ans2 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{''.join(map(str, answer.args[:-1]))}({answer.args[-1]})"))
        return tuple([(ans1, hint), (ans2, hint)])
        
    else:
        ans1 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"({'*'.join(map(str, answer.args[:-1]))})({answer.args[-1]})"))
        ans2 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{'*'.join(map(str, answer.args[:-1]))}({answer.args[-1]})"))
        return tuple([(ans1, hint), (ans2, hint)])

def gcf_2_factor(second_part):
    x = symbols('x')
    second_part = parse_latex(second_part)
    answer = sp.factor(second_part)
    hint = latex(answer)
    if answer.args[1] == 2:
        answer = f"{answer.args[0]}"
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', answer))
        return tuple([(answer, hint)])
        
    elif len(answer.args) == 2:
        ans1 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{answer.args[0]}*({answer.args[1]})"))
        ans2 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{answer.args[0]}({answer.args[1]})"))
        return tuple([(ans1, hint), (ans2, hint)])
        
    else:
        ans1 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"({'*'.join(map(str, answer.args[:-1]))})({answer.args[-1]})"))
        ans2 = re.compile(re.sub(r'([-+()*])', r'\\\1', f"{'*'.join(map(str, answer.args[:-1]))}({answer.args[-1]})"))
        return tuple([(ans1, hint), (ans2, hint)])

def gcf_1_final(init_value):
    x = symbols('x')
    equation = parse_latex(init_value)
    factors = sp.factor(equation)
    if factors.args[1] == 2:
        answer = factors.args[0]
        hint = latex(answer)
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
        return tuple([(answer, hint)])
    else:
        facts = list()
        for factor in factors.args:
            answer = factor
            hint = latex(answer)
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
            facts.append((answer, hint))
        return tuple(facts)
    
def gcf_2_final(init_value, gcf_1_final):
    equation = sp.factor(parse_latex(init_value))
    first_part = parse_latex(gcf_1_final)
    answer = sp.div(equation, first_part)[0]
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def final_answer(init_value):
    equation = parse_latex(init_value)
    answer = sp.factor(equation)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

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

    'ac_value': Operator(head=('ac_value', V('equation'), V('kc')),
                         precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                         effects=[Fact(field='ac_value', value=(ac_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_1_b': Operator(head=('factor_1_b', V('equation'), V('kc')),
                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                           effects=[Fact(field='factor_1_b', value=(factor_1_b, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_2_b': Operator(head=('factor_2_b', V('equation'), V('f1'), V('kc')),
                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                         Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True),
                           effects=[Fact(field='factor_2_b', value=(factor_2_b, V('eq'), V('f1eq')), kc=V('kc'), answer=True)],
    ),

    'sum_factor': Operator(head=('sum_factor', V('f1'), V('f2'), V('kc')),
                            precondition=Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True)&
                                         Fact(field=V('f2'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                            effects=[Fact(field='sum_factor', value=(sum_factor, V('f1eq'), V('f2eq')), kc=V('kc'), answer=True)],
    ),

    'sum_c': Operator(head=('sum_c', V('equation'), V('sum_factor'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                     Fact(field=V('sum_factor'), value=V('sum_factor_eq'), kc=V('sum_factor_kc'), answer=True),
                        effects=[Fact(field='sum_c', value=(sum_c, V('eq'), V('sum_factor_eq')), kc=V('kc'), answer=True)],
    ),

    'p_value': Operator(head=('p_value', V('factor_1_b'), V('factor_2_b'), V('kc')),
                        precondition=Fact(field=V('factor_1_b'), value=V('f1'), kc=V('f1kc'), answer=True)&
                                        Fact(field=V('factor_2_b'), value=V('f2'), kc=V('f2kc'), answer=True),
                        effects=[Fact(field='p_value', value=(p_value, V('f1'), V('f2')), kc=V('kc'), answer=True)],
    ),

    'q_value': Operator(head=('q_value', V('factor_1_b'), V('factor_2_b'), V('p_value'), V('kc')),
                        precondition=Fact(field=V('factor_1_b'), value=V('f1'), kc=V('f1kc'), answer=True)&
                                        Fact(field=V('factor_2_b'), value=V('f2'), kc=V('f2kc'), answer=True)&
                                        Fact(field=V('p_value'), value=V('p'), kc=V('pkc'), answer=True),
                        effects=[Fact(field='q_value', value=(q_value, V('f1'), V('f2'), V('p')), kc=V('kc'), answer=True)],
    ),  

    'first_part': Operator(head=('first_part', V('equation'), V('p_value'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                            Fact(field=V('p_value'), value=V('p'), kc=V('pkc'), answer=True),
                            effects=[Fact(field='first_part', value=(first_part, V('eq'), V('p')), kc=V('kc'), answer=True)],
    ),

    'second_part': Operator(head=('second_part', V('equation'), V('q_value'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                            Fact(field=V('q_value'), value=V('q'), kc=V('qkc'), answer=True),
                            effects=[Fact(field='second_part', value=(second_part, V('eq'), V('q')), kc=V('kc'), answer=True)],
    ),

    'gcf_1_factor': Operator(head=('gcf_1_factor', V('first_part'), V('kc')),
                            precondition=Fact(field=V('first_part'), value=V('eq'), kc=V('fkc'), answer=True),
                            effects=[Fact(field='gcf_1_factor', value=(gcf_1_factor, V('eq')), kc=V('kc'), answer=True)],
    ),

    'gcf_2_factor': Operator(head=('gcf_2_factor', V('second_part'), V('kc')),
                            precondition=Fact(field=V('second_part'), value=V('eq'), kc=V('fkc'), answer=True),
                            effects=[Fact(field='gcf_2_factor', value=(gcf_2_factor, V('eq')), kc=V('kc'), answer=True)],
    ),

    'gcf_1_final': Operator(head=('gcf_1_final', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='gcf_1_final', value=(gcf_1_final, V('eq')), kc=V('kc'), answer=True)],
    ),

    'gcf_2_final': Operator(head=('gcf_2_final', V('equation'), V('gcf_1_final'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                        Fact(field=V('gcf_1_final'), value=V('gcf_1_final_eq'), kc=V('gcf_1_final_kc'), answer=True),
                            effects=[Fact(field='gcf_2_final', value=(gcf_2_final, V('eq'), V('gcf_1_final_eq')), kc=V('kc'), answer=True)],
    ),

    'final_answer': Operator(head=('final_answer', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='final_answer', value=(final_answer, V('eq')), kc=V('kc'), answer=True)],
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
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('p_value', 'factor_1_b', 'factor_2_b', ('p_value',)), primitive=True),
                            Task(head=('q_value', 'factor_1_b', 'factor_2_b', 'p_value', ('q_value',)), primitive=True),
                            Task(head=('first_part', V('equation'), 'p_value', ('first_part',)), primitive=True),
                            Task(head=('second_part', V('equation'), 'q_value', ('second_part',)), primitive=True),
                            Task(head=('gcf_1_factor', 'first_part', ('gcf_1_factor',)), primitive=True),
                            Task(head=('gcf_2_factor', 'second_part', ('gcf_2_factor',)), primitive=True),
                            Task(head=('gcf_1_final', V('equation'), ('gcf_1_final',)), primitive=True),
                            Task(head=('gcf_2_final', V('equation'), 'gcf_1_final', ('gcf_2_final',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('p_value', 'factor_1_b', 'factor_2_b', ('p_value',)), primitive=True),
                            Task(head=('q_value', 'factor_1_b', 'factor_2_b', 'p_value', ('q_value',)), primitive=True),
                            Task(head=('first_part', V('equation'), 'p_value', ('first_part',)), primitive=True),
                            Task(head=('second_part', V('equation'), 'q_value', ('second_part',)), primitive=True),
                            Task(head=('gcf_1_factor', 'first_part', ('gcf_1_factor',)), primitive=True),
                            Task(head=('gcf_2_factor', 'second_part', ('gcf_2_factor',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('p_value', 'factor_1_b', 'factor_2_b', ('p_value',)), primitive=True),
                            Task(head=('q_value', 'factor_1_b', 'factor_2_b', 'p_value', ('q_value',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True),
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}
