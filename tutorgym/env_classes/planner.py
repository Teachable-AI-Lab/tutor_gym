from copy import deepcopy
from typing import List, Tuple, Set, Dict, Union, Generator
from shop2.domain import Task, Axiom, Method, flatten
from shop2.utils import replaceHead, replaceTask, removeTask, getT0, generatePermute
from shop2.fact import Fact
from shop2.conditions import AND

def planner(state:Fact, T: Union[List, Tuple], D: Dict, debug: bool = False) -> Generator:
    cstate = state
    stack, visited, correctpath = list(), list(), list()
    stack.append((deepcopy(T), deepcopy(state)))
    correctpath.append((deepcopy(stack), deepcopy(visited)))

    while True:
        cstate = state 
        if not T:
            yield (Fact(status="Done"), state)

        T0 = getT0(T)
        task = T0[0]

        if task.primitive:
            result = D[task.name].applicable(task, state, debug)
            if result:
                del_effects, add_effects = result
                state, correct, effect = yield (list(add_effects).pop(), state)
                if state != cstate:
                    stack = [(xt, state) for xt, xs in stack]
                    correctpath = [(deepcopy(stack), deepcopy(visited))]
                    continue
                elif correct:
                    T = removeTask(T, task)
                    for effect in del_effects: state = state & ~effect
                    for effect in add_effects: state = state & effect
                    stack = [(deepcopy(T), deepcopy(state))]
                    correctpath = [(deepcopy(stack), deepcopy(visited))]
                else:
                    if stack:
                        T, state = stack.pop()
                        state = AND(*flatten(state))
                    else:
                        stack, visited = correctpath.pop()
                        if not correctpath:
                            correctpath.append((deepcopy(stack), deepcopy(visited)))
                        T, state = stack.pop()
                        state = AND(*flatten(state))
                        stack.append((deepcopy(T), deepcopy(state)))
                        state, correct = yield (False, state)
                    # yield from backtrack()
            else:
                if stack:
                    T, state = stack.pop()
                    state = AND(*flatten(state))
                else:
                    stack, visited = correctpath.pop()
                    if not correctpath:
                        correctpath.append((deepcopy(stack), deepcopy(visited)))
                    T, state = stack.pop()
                    state = AND(*flatten(state))
                    stack.append((deepcopy(T), deepcopy(state)))
                    state, correct = yield (False, state)
                # yield from backtrack()
        else:
            result = D[task.name].applicable(task, state, str(), visited, debug)
            if result:
                subtask = result
                T = type(T)([subtask])+removeTask(T, task)
                permutations = generatePermute(T)
                for t in reversed(permutations):
                    stack.append((t, deepcopy(state)))
            else:
                if stack:
                    T, state = stack.pop()
                    state = AND(*flatten(state))
                else:
                    stack, visited = correctpath.pop()
                    if not correctpath:
                        correctpath.append((deepcopy(stack), deepcopy(visited)))
                    T, state = stack.pop()
                    state = AND(*flatten(state))
                    stack.append((deepcopy(T), deepcopy(state)))
                    state, correct = yield (False, state)
