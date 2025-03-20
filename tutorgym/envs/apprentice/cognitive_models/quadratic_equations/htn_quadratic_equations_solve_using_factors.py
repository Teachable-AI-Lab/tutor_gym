import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V


def htn_quadratic_equations_solve_using_factors_problem():
    x = sp.symbols('x')
    x1, x2, coeff = 0, 0, 0
    while not (x1*x2) or not coeff:
        x1, x2 = randint(-10, 10), randint(-10, 10)
        factorlist = [f for factor in sp.divisors(int(x1)) for f in (factor, -factor) if (f*x2+x1) 
                                                                                    and abs((f*x1+x2)/f)/(2*sp.sqrt(abs(x1*x2/f)))!=1]
        if factorlist: 
            coeff = choice(factorlist)
    terms = [coeff*x*x, coeff*x*(-x1), (-x2)*x, (-x1)*(-x2)]
    equation = "+".join(map(str, terms)).replace("+-", "-").replace("x**2", "x^{2}").replace("*", "")
    equation = f"{equation}=0"
    return equation

def factorized_form(init_value):
    facts = list()
    const, factors = sp.factor((parse_latex(init_value)).lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (*factors, 1)
    for i in range(2):
        equation = sp.Eq(sp.Mul(const, factors[i])*factors[(i+1)%2], 0)
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
        hint = f"{equation.lhs}={equation.rhs}".replace("*", "")
        facts.append((answer, hint))
    return tuple(facts)

def first_equation(init_value):
    facts = list()
    const, factors = sp.factor((parse_latex(init_value)).lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (*factors, 1)
    for i in range(2):
        factorized = sp.Eq(sp.Mul(const, factors[i])*factors[(i+1)%2], 0)
        for factor in factorized.lhs.as_coeff_mul()[1]:
            equation = sp.Eq(factor,0)  
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))    
            hint = f"{equation.lhs}={equation.rhs}"
            facts.append((answer, hint))
    return tuple(facts)

def second_equation(init_value, factor):
    fact = list()
    const, factors = sp.factor((parse_latex(init_value)).lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (*factors, 1)
    for i in range(2):
        equation = sp.Mul(const, factors[i])*factors[(i+1)%2]
        feq = parse_latex(factor).lhs
        quotient = sp.Eq(sp.div(equation, feq)[0],0)
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(quotient, order="grlex")))
        hint = f"{quotient.lhs}={quotient.rhs}"
        fact.append((answer, hint))
    return tuple(fact)

def first_root(init_value):
    x = symbols("x")
    facts = list()
    const, factors = sp.factor((parse_latex(init_value)).lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (*factors, 1)
    for i in range(2):
        factorized = sp.Eq(sp.Mul(const, factors[i])*factors[(i+1)%2], 0)
        for factor in factorized.lhs.as_coeff_mul()[1]:
            equation = sp.Eq(factor,0)  
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))    
            root = sp.sstr(sp.solve(equation, x)[0], order="grlex")
            answer = re.compile(root)
            hint = root
            facts.append((answer, hint))
    return tuple(facts)
    

def second_root(init_value, factor):
    x = symbols("x")
    fact = list()
    const, factors = sp.factor((parse_latex(init_value)).lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (*factors, 1)
    for i in range(2):
        equation = sp.Mul(const, factors[i])*factors[(i+1)%2]
        feq = parse_latex(factor)
        quotient = sp.Eq(sp.div(equation, feq)[0],0)
        root = sp.sstr(sp.solve(quotient, x)[0], order="grlex")
        answer = re.compile(root)
        hint = root
        fact.append((answer, hint))
    return tuple(fact)
    

def update_product_value(init_value):
    n, m = re.findall(r'\d+', init_value)
    answer = parse_latex(f"\\sqrt{{{int(n)*int(m)}}}")
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    hint = f"\\sqrt{{{int(n)*int(m)}}}"
    return tuple([(answer, hint)])

def simplify_product_value(init_value):
    n, m = re.findall(r'\d+', init_value)

    answer = sp.Mul(sp.sqrt(int(n))*sp.sqrt(int(m)))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(answer, order="grlex")))
    hint = f"{sp.Mul(sp.sqrt(int(n))*sp.sqrt(int(m)))}"
    return tuple([(answer, hint)])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
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
                                                Fact(field=V('factor'), value=V('feq'), kc=V('fkc'), answer=True),
                                effects=[Fact(field='second_equation', value=(second_equation, V('eq'), V('feq')), kc=V('kc'), answer=True)],
    ),

    'first_root': Operator(head=('first_root', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='first_root', value=(first_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_root': Operator(head=('second_root', V('equation'), V('factor'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                                Fact(field=V('factor'), value=V('feq'), kc=V('fkc'), answer=True),
                                effects=[Fact(field='second_root', value=(second_root, V('eq'), V('feq')), kc=V('kc'), answer=True)],
    ),


    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('factorized_form', V('equation'), ('factorized_form',)), primitive=True),
                            Task(head=('first_equation', V('equation'), ('first_equation',)), primitive=True),
                            Task(head=('second_equation', V('equation'), 'first_equation', ('second_equation',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_equation', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('factorized_form', V('equation'), ('factorized_form',)), primitive=True),
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_equation', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('first_root', V('equation'), ('first_root',)), primitive=True),
                            Task(head=('second_root', V('equation'), 'first_root', ('second_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}