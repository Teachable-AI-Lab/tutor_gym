from random import randint
from random import choice
from pprint import pprint
import logging, operator
from functools import reduce

import cv2  # pytype:disable=import-error
from PIL import Image, ImageDraw
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
from tutorenvs.utils import OnlineDictVectorizer
import numpy as np
from colorama import Back, Fore
import json
import os
import re

from tutorenvs.utils import DataShopLogger
# from tutorenvs.utils import StubLogger
# from tutorenvs.fsm import StateMachine

from tutorenvs.std import ProblemState, Action, FiniteStateMachine, StateMachineTutor

class Algebra(StateMachineTutor):
    def __init__(self, n_rows=3, var_denoms=True, one_coeffs=False, **kwargs):
        """
        Creates a state and sets a random problem.
        """
        super().__init__(**kwargs)
        self.n_rows = n_rows
        self.one_coeffs = one_coeffs
        # self.logger.set_student()

        this_dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(this_dir,"algebra.json")
        with open(path,'r') as f:
            self.problems = json.load(f)

        self.var_denoms = var_denoms
        if(not self.one_coeffs):
            proc_nm = lambda x: re.sub(r"(-?)1([a-zA-z])", "\g<1>\g<2>", x)
            self.problems = {proc_nm(k):v for k,v in self.problems.items()}

        if(not var_denoms):
            self.problems = {k:v for k,v in self.problems.items()
                             if len(re.findall(r"\/\d*[a-z]?", k)) == 0}

            # print(self.problems.keys())

        print([x for x in self.problems.keys()])

        from random import sample
        print(sample([tuple(x.split("=")) for x in self.problems.keys()], 50))
        self.set_random_problem()
        

    def _blank_state(self, n_rows):
        field_params = {'type': 'TextField', 
                        "locked" : False,
                        "value" : "",
                        "width" : 100, "height" : 40, }
        button_params = {'type': 'Button', "width" : 100, "height" : 100, }
        state = {}
        for row in range(n_rows):
            state[f'lhs{row}'] = {'x' : 0, 'y' : row * 50, **field_params}
            state[f'rhs{row}'] = {'x' : 110, 'y' : row * 50, **field_params}
            state[f'step{row}'] = {'x' : 220, 'y' : row * 50, **field_params}
            if(row == 0):
                state[f'lhs{row}']['locked'] = True
                state[f'rhs{row}']['locked'] = True

        state['done'] = {'x': 0, 'y': self.n_rows * 50, **button_params}

        # Ensure all have an id attribute
        for key, obj in state.items():
            state[key]['id'] = key

        
        # self.possible_selections = ?
        # self.possible_args = ?

        return ProblemState(state)

    def set_start_state(self, lhs, rhs, **kwargs):
        ''' Domain implementation: Used by StateMachineTutor.set_problem() 
            to initialize a start state.'''

        

        state = self._blank_state(self.n_rows)
        state["lhs0"]["value"] = lhs
        state["rhs0"]["value"] = rhs
        self.start_state = ProblemState(state)
        self.problem_name = f"{lhs}={rhs}"
        self.problem = self.problems[self.problem_name]
        # self.problem_type = ptype

    def set_random_problem(self):
        prob_name = choice(list(self.problems.keys()))
        prob = self.problems[prob_name]
        args = prob_name.split("=")
        self.set_problem(*args)

        # Print sequence
        while(not self.is_done):
            action = self.get_demo()
            print("+++", action.sai, action.args)
            self.apply(action)

        self.set_problem(*args)

    def _operand_in(self, operand, part):
        matches = re.findall(f"(?<!-)(?<!\d)({operand})", part)
        print("matches", matches)
        return len(matches) > 0
        # if(operand in part):
        #     if(operand[0] != "-"
        #        and f"-{operand}" in other):
        #         return False
        #     return True
        # return False

    def _infer_args(self, step, curr_state):
        kind = step['KC (Action-typein)']
        sel, _, inp = step['sai']
        if('step' in sel):
            step_num = sel[-1]
            # split inputs like 'multiply x' -> ('multiply', 'x')
            act_str, operand = inp.split(" ")
            left = curr_state['lhs'+step_num]['value']
            right = curr_state['rhs'+step_num]['value']

            if(act_str in ("multiply", "divide")):
                if(len(re.findall(r"[a-zA-z]", left))):
                    if(self._operand_in(operand, left)
                       or operand in ("1","-1")):
                        return ['lhs'+step_num]

                if(len(re.findall(r"[a-zA-z]", right))):
                    if(self._operand_in(operand, right) or
                        operand in ("1","-1")):
                        return ['rhs'+step_num]
            else:
                if(self._operand_in(operand, left)):
                    return ['lhs'+step_num]
                elif(self._operand_in(operand, right)):
                    return ['rhs'+step_num]
            
            raise ValueError(f"For problem {self.problem_name} at state:{left}={right} arguments for step with inp={inp} could not be resolved")

        elif("lhs" in sel or "rhs" in sel):
            step_num = sel[-1]
            l_or_r = sel[:-1]
            prev_num = int(step_num)-1
            return [f"{l_or_r}{prev_num}", f"step{prev_num}"]
        elif(sel == "done"):
            return []
        else:
            raise ValueError(f"Unrecognized selection {sel}")

    def create_fsm(self, state):
        curr_state = state.copy()
        fsm = FiniteStateMachine(curr_state)

        has_done = False
        grouped_steps = [[] for i in range(2*self.n_rows+1)]
        for step in self.problem['steps']:
            sel = step['sai'][0]
            if(sel == 'done'):
                has_done = True
                _s,_a,_i = step['sai']
                step['sai'] = (_s, _a, int(_i))
                grouped_steps[-1].append(step)
            else:
                row = int(sel[-1])
                offset = 0 if "step" in sel else 1  
                grouped_steps[2*row-offset].append(step)

        if(not has_done):
            raise ValueError("Problem has no done state!")

        # print("::", [len(g) for g in grouped_steps])
        for i, group in enumerate(grouped_steps):
            # print(i,":")
            if(len(group) == 0):
                continue
            actions = []

            skip_group = False

            for step in group:
                # print('\t',step)
                sel, act_type, inp = step['sai']
                args = self._infer_args(step, curr_state)

                if(not self.one_coeffs):
                    if(inp == "divide 1"):
                        skip_group = True
                        break
                    if(isinstance(inp, str) and
                        re.match(r"-?1[a-zA-z]", inp)):
                        inp = inp.replace("1", "")

                inputs = {'value': inp}
                a = Action((sel, act_type, inputs), args=args)
                actions.append(a)

            #     if(isinstance(inp, str)):
            #         # If is pattern like -1x, then also allow -x
            #         if(re.match(r"-1[a-zA-Z]", inp)):
            #             a = Action((sel, act_type, {'value': f"-{inp[-1]}"}), args=args)
            #             actions.append(a)

            #         # If is pattern like -x, then also allow -1x
            #         if(re.match(r"-[a-zA-Z]", inp)):
            #             a = Action((sel, act_type, {'value': f"-1{inp[-1]}"}), args=args)
            #             actions.append(a)

            # if(len(actions) == 3):
            #     print("MOOP", actions)
            #     raise ValueError()
            # print(len(actions))
            if(not skip_group):
                curr_state = fsm.add_unordered(curr_state, actions)
            else:
                print("FORCE DONE")
                done_act = Action(("done", "PressButton", {'value': -1},), how_str="-1", args=args)
                curr_state = fsm.add_unordered(curr_state, [done_act])
                break


        # act = Action(('done', "PressButton", {'value': -1}), how_str="-1")
        # curr_state = fsm.add_edge(curr_state, act)
        return fsm

    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args


def test_basic():
    alg = Algebra(demo_args=True)
    alg.set_problem("10", "2+2x")
    for i in range(8):
        action = alg.get_demo()
        print(action, action.args)
        reward = alg.check(action)
        nxt = alg.get_all_demos()
        # assert len(nxt) <= 2

        # if(i != 7):
        #     assert mc.check(('done','PressButton', {"value": -1})) == -1
        #     assert not mc.is_done
        alg.apply(action)
        # print(action, mc.state)
    # assert mc.is_done
    # assert mc.state["out1"]['value'] == "6"
    # assert mc.state["out2"]['value'] == "5"
    # assert mc.state["out3"]['value'] == "2"
    # assert mc.state["out4"]['value'] == "1"

if __name__ == "__main__":
    test_basic()

