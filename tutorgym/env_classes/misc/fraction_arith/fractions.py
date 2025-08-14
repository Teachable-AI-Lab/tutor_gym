from random import randint
from random import choice
from pprint import pprint
import logging, operator
from functools import reduce

import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
from tutorgym.utils import OnlineDictVectorizer
import numpy as np
from colorama import Back, Fore

from tutorgym.utils import DataShopLogger
# from tutorgym.utils import StubLogger
# from tutorgym.fsm import StateMachine

from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel


class FractionArithmetic(StateMachineTutor):
    def __init__(self, n_fracs=2, problem_types=["AD", "AS", "M"], **kwargs):
        """
        Creates a state and sets a random problem.
        """
        if n_fracs < 2:
            raise Exception("n cannot be lower than 2.")
        super().__init__(action_model=CTAT_ActionModel, **kwargs)
        self.n = self.n_fracs = n_fracs
        self.problem_types = problem_types
        # self.logger.set_student()
        self.set_random_problem()

    def _blank_state(self, op, N):
        start_params = {'type': 'TextField', "locked" : True, "value" : "", "width" : 100, "height" : 100, }
        field_params = {'type': 'TextField', "locked" : False, "value" : "", "width" : 100, "height" : 100, }
        button_params = {'type': 'Button', "width" : 100, "height" : 100, }

        state = {}

        # Make initial fraction problem
        for i in range(N):
            offset = (i) * 220

            # Position each fraction box
            state.update({
                f"init_num{i+1}" : {"x" :offset,   "y" : 110 ,  **start_params},
                f"init_den{i+1}" : {"x" :offset,   "y" : 220 ,  **start_params},
            })

            # Position each operator box
            if(i > 0):
                state.update({
                    f"init_op{i}" : {"x" :offset-110,   "y" : 160 , **start_params, "value" : op},
                })

        state.update({"check_convert" : {"x" : 0, "y" : 330 , **field_params}})

        # Make conversion area
        for i in range(N):
            offset = (i) * 220
            
            # Position each fraction box
            state.update({
                f"conv_num{i+1}" : {"x" :offset,   "y" : 440 ,  **field_params},
                f"conv_den{i+1}" : {"x" :offset,   "y" : 550 ,  **field_params},
            })

            # Position each operator box
            if(i > 0):
                state.update({
                    f"conv_op{i}" : {"x" :offset-110,   "y" : 490 , **start_params, "value" : op},
                })

        # Make Answer area
        state.update({
            # f"equals" : {"x" : N*220-110,   "y" : 110 , "value" : "=", **start_params},
            f"ans_num" : {"x" : N*220,   "y" : 440 ,  **field_params},
            f"ans_den" : {"x" : N*220,   "y" : 550 ,  **field_params},
            "done" :     {"x" : N*220, "y" : N*220+210 , **button_params},
        })

        self.init_nums = [f'init_num{i+1}' for i in range(N)]
        self.init_dens = [f'init_den{i+1}' for i in range(N)]
        # init_ops = [f'init_op{i+1}' for i in range(N-1)]
        self.conv_nums = [f'conv_num{i+1}' for i in range(N)]
        self.conv_dens = [f'conv_den{i+1}' for i in range(N)]
        # conv_ops = [f'conv_op{i+1}' for i in range(N-1)]
        self.possible_selections = self.conv_nums + self.conv_dens + ['ans_num', 'ans_den', 'done']
        self.possible_args = self.init_nums + self.init_dens + self.conv_nums + self.conv_dens

        # print("POSSIBLE SELECTIONS", self.possible_selections)
        # print("POSSIBLE ARGS", self.possible_args)
        # Ensure all have an id attribute
        for key, obj in state.items():
            state[key]['id'] = key
        return ProblemState(state)

    def action_is_done(self, action):
        return action.selection == "done"

    def set_start_state(self, op, fracs, **kwargs):
        ''' Domain implementation: Used by StateMachineTutor.set_problem() 
            to initialize a start state.'''
        state = self._blank_state(op, len(fracs))
        for i, (num, den) in enumerate(fracs):
            state[f'init_num{i+1}']['value'] = str(num)
            state[f'init_den{i+1}']['value'] = str(den)
        self.start_state = ProblemState(state)

        ptype = "M"
        if(op == "+"):
            ptype = "AS" if len(set([den for num,den in fracs])) == 1 else "AD"

        print("ptype", ptype)
        self.problem_name = ptype+"_" + op.join([f"{num}/{den}" for num, den in fracs])
        self.problem_type = ptype
        self.problem = (op, fracs) 

        # print("CURR STATE:")
        # for key, obj in state.objs.items():
        #     print(key, obj)

    def set_random_problem(self, ptype=None):
        ok = False
        if(ptype is None):
            ptype = choice(self.problem_types)
        

        print("<<", ptype, self.problem_types)

        if(ptype == "AD" or ptype == "M"):
            while(not ok):
                nums = [str(randint(1, 15)) for _ in range(self.n)]
                dens = [str(randint(2, 15)) for _ in range(self.n)]
                ok = (not any(np.array(nums)==np.array(dens))) and (len(set(dens)) > 1)
            operator = "+" if ptype == "AD" else "*" #choice(['+', '*'])
        elif(ptype == "AS"):
            nums = [str(randint(1, 15)) for _ in range(self.n)]
            dens = [str(randint(2, 15))] * self.n
            operator = "+"
        # print("NUMERATORS", nums)
        # print("DENOMINATORS", dens)
        print("<<", list(zip(nums, dens)))
        self.set_problem(operator, list(zip(nums, dens)))
        return {"op" : operator,
                "fracs" : list(zip(nums, dens))}
        # print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {operator.join([f'({n}/{v})' for n,v in zip(nums,dens)])}" )

    def create_fsm(self, state, **kwargs):
        curr_state = state#.copy()
        # print("CURR STATE", state)
        fsm = FiniteStateMachine(curr_state, self.action_model)

        init_num_vals = [int(state[f'init_num{i+1}']['value']) for i in range(self.n)]
        init_den_vals = [int(state[f'init_den{i+1}']['value']) for i in range(self.n)]

        if(self.problem_type == "M"):            
            num = str(reduce(operator.mul, init_num_vals))
            num_sai = (f'ans_num', 'UpdateTextField', num)
            num_act = Action(num_sai, arg_foci=self.init_nums, how_help="Multiply(a,b)")

            den = str(reduce(operator.mul, init_den_vals))
            den_sai = (f'ans_den', 'UpdateTextField', den)
            den_act = Action(den_sai, arg_foci=self.init_dens, how_help="Multiply(a,b)")

            curr_state = fsm.add_unordered(curr_state, [num_act, den_act])
        elif(self.problem_type == "AS"):
            num = str(reduce(operator.add, init_num_vals))
            num_sai = (f'ans_num', 'UpdateTextField', num)
            num_act = Action(num_sai, arg_foci=self.init_nums, how_help="Add(a,b)")

            den = str(init_den_vals[0])
            den_sai = (f'ans_den', 'UpdateTextField', den)
            den_act = Action(den_sai, arg_foci=['init_den1'], how_help="Copy(a)")

            curr_state = fsm.add_unordered(curr_state, [num_act, den_act])
        else:
            # Addition Different
            sai = ('check_convert', 'UpdateTextField', 'x')
            curr_state = fsm.add_edge(curr_state, 
                Action(sai, arg_foci=[], how_help="'x'"))

            # Common denominator by multiplying together
            conv_den_val = reduce(operator.mul, init_den_vals)
            den_acts = []
            for i in range(self.n):
                sai = (f'conv_den{i+1}', 'UpdateTextField', str(conv_den_val))
                den_acts.append(Action(sai, arg_foci=self.init_dens, how_help="Multiply(a, b)"))
            
            

            # Convert numerators
            num_acts = []
            conv_num_vals = []
            for i in range(self.n):
                conv_num_val = int((conv_den_val * init_num_vals[i]) / init_den_vals[i])
                conv_num_vals.append(conv_num_val)
                sai = (f'conv_num{i+1}', 'UpdateTextField', str(conv_num_val))

                if(self.n_fracs == 2):
                    # Butterfly Method
                    j = 0 if i == 1 else 1
                    arg_foci = [f"init_num{i+1}", f"init_den{j+1}"]
                    num_acts.append(Action(sai, arg_foci=arg_foci, how_help="Multiply(a, b)"))
                else:
                    arg_foci = [f"conv_den{i+1}", f"init_num{i+1}", f"init_den{i+1}"]
                    raise NotImplemented("TODO Didn't make it into the refactor")
                
            
            if(self.n_fracs == 2):
                curr_state = fsm.add_unordered(curr_state, den_acts+num_acts)
            else:
                curr_state = fsm.add_unordered(curr_state, den_acts)
                curr_state = fsm.add_unordered(curr_state, num_acts)

            # Add final 
            num = str(reduce(operator.add, conv_num_vals))
            num_sai = (f'ans_num', 'UpdateTextField', num)
            num_act = Action(num_sai, arg_foci=self.conv_nums, how_help="Add(a,b)")

            den = str(conv_den_val)
            den_sai = (f'ans_den', 'UpdateTextField', den)
            den_act = Action(den_sai, arg_foci=[f'conv_den{self.n}'], how_help="Copy(a)")

            curr_state = fsm.add_unordered(curr_state, [num_act, den_act])

        act = Action(('done', "PressButton", -1), how_help="-1")
        curr_state = fsm.add_edge(curr_state, act)
        return fsm

    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args

# class FractionArithNumberEnv(gym.Env):
#     metadata = {'render.modes': ['human']}

#     def __init__(self):
#         self.tutor = FractionArithSymbolic()
#         n_selections = len(self.tutor.get_possible_selections())
#         n_features = 900
#         self.dv = OnlineDictVectorizer(n_features)
#         self.observation_space = spaces.Box(
#             low=0.0, high=1.0, shape=(1, n_features), dtype=np.float32)
#         self.action_space = spaces.MultiDiscrete([n_selections, 450])
#         self.n_steps = 0
#         self.max_steps = 100000

#     def step(self, action):
#         self.n_steps += 1

#         s, a, i = self.decode(action)
#         # print("STEP", s, a, i)
#         # print()
#         reward = self.tutor.apply_sai(s, a, i)
#         # self.render()
#         # print(reward)
#         state = self.tutor.state
#         # pprint(state)
#         obs = self.dv.fit_transform([state])[0]
#         done = (s == 'done' and reward == 1.0)

#         # have a max steps for a given problem.
#         # When we hit that we're done regardless.
#         if self.n_steps > self.max_steps:
#             done = True

#         info = {}

#         return obs, reward, done, info

#     def encode(self, sai):
#         s,a,inp = sai
        
#         out = np.zeros(1,dtype=np.int64)
#         enc_s = self.tutor.get_possible_selections().index(s)
#         if(s == 'done' or s == "check_convert"):
#             v = 0
#         else:
#             v = int(inp) - 1
#         # n = len(self.tutor.get_possible_selections()) 
#         out[0] = 450 * enc_s + int(v) 
#         return out

#     def request_demo_encoded(self):
#         action = self.tutor.request_demo() 
#         # print("DEMO ACTION:", action)
#         return self.encode(action)


#     def decode(self, action):
#         # print(action)
#         s = self.tutor.get_possible_selections()[action[0]]

#         if s == "done":
#             a = "ButtonPressed"
#         else:
#             a = "UpdateField"

#         if s == "done":
#             v = -1
#         if s == "check_convert":
#             v = "x"
#         else:
#             v = action[1] + 1

#         i = str(v)
#         # print(s,a,i)
#         return s, a, i

#     def reset(self):
#         self.n_steps = 0
#         self.tutor.set_random_problem()
#         # self.render()
#         state = self.tutor.state
#         obs = self.dv.fit_transform([state])[0]
#         return obs

#     def render(self, mode='human', close=False):
#         self.tutor.render()


# class FractionArithDigitsEnv(gym.Env):
#     metadata = {'render.modes': ['human']}

#     def get_rl_state(self):
#         # self.state = {
#         #     'initial_num_left': num1,
#         #     'initial_denom_left': denom1,
#         #     'initial_operator': operator,
#         #     'initial_num_right': num2,
#         #     'initial_denom_right': denom2,
#         #     'check_convert': '',
#         #     'convert_num_left': '',
#         #     'conv_den_val_left': '',
#         #     'convert_operator': operator,
#         #     'convert_num_right': '',
#         #     'conv_den_val_right': '',
#         #     'answer_num': '',
#         #     'answer_denom': '',
#         # }

#         state = {}
#         for attr in self.tutor.state:
#             if attr == "initial_operator" or attr == "convert_operator":
#                 state[attr] = self.tutor.state[attr]
#                 continue

#             state[attr + "[0]"] = ""
#             state[attr + "[1]"] = ""
#             state[attr + "[2]"] = ""

#             if self.tutor.state[attr] != "":
#                 l = len(self.tutor.state[attr])

#                 if l > 2:
#                     state[attr + "[0]"] = self.tutor.state[attr][-3]
#                 if l > 1:
#                     state[attr + "[1]"] = self.tutor.state[attr][-2]

#                 state[attr + "[2]"] = self.tutor.state[attr][-1]

#             # print(self.tutor.state[attr])
#             # pprint(state)

#         return state

#     def __init__(self):
#         self.tutor = FractionArithSymbolic()
#         n_selections = len(self.tutor.get_possible_selections())
#         n_features = 10000
#         self.feature_hasher = FeatureHasher(n_features=n_features)

#         self.observation_space = spaces.Box(low=0.0,
#                 high=1.0, shape=(1, n_features), dtype=np.float32)
#         self.action_space = spaces.MultiDiscrete([n_selections, 10, 10, 10])

#     def step(self, action):
#         s, a, i = self.decode(action)
#         # print(s, a, i)
#         # print()
#         reward = self.tutor.apply_sai(s, a, i)
#         # print(reward)
        
#         state = self.get_rl_state()
#         # pprint(state)
#         obs = self.feature_hasher.transform([state])[0].toarray()
#         done = (s == 'done' and reward == 1.0)
#         info = {}

#         return obs, reward, done, info

#     def decode(self, action):
#         # print(action)
#         s = self.tutor.get_possible_selections()[action[0]]

#         if s == "done":
#             a = "ButtonPressed"
#         else:
#             a = "UpdateField"
        
#         if s == "done":
#             v = -1
#         if s == "check_convert":
#             v = "x"
#         else:
#             v = action[1]
#             v += 10 * action[2]
#             v += 100 * action[3]
#         # if action[4]:
#         #     v *= -1
#         i = str(v)

#         return s, a, i

#     def reset(self):
#         self.tutor.set_random_problem()
#         state = self.get_rl_state()
#         obs = self.feature_hasher.transform([state])[0].toarray()
#         return obs

#     def render(self, mode='human', close=False):
#         self.tutor.render()


# class FractionArithOppEnv(gym.Env):
#     metadata = {'render.modes': ['human']}

#     def __init__(self):
#         self.tutor = FractionArithSymbolic()
#         n_selections = len(self.tutor.get_possible_selections())
#         n_features = 2000
#         n_operators = len(self.get_rl_operators())
#         n_args = len(self.tutor.get_possible_args())
#         self.dv = OnlineDictVectorizer(n_features)
#         self.observation_space = spaces.Box(
#             low=0.0, high=1.0, shape=(1, n_features), dtype=np.float32)
#         self.action_space = spaces.MultiDiscrete([n_selections, n_operators,
#             n_args, n_args])
#         self.n_steps = 0
#         self.max_steps = 100000


#     def get_rl_operators(self):
#         return ['copy',
#                 'add',
#                 'multiply']

#     def get_rl_state(self):
#         state = self.tutor.state.copy()
#         for attr in self.tutor.state:
#             for attr2 in self.tutor.state:
#                 if attr == "initial_operator" or attr == "convert_operator":
#                     continue
#                 if attr2 == "initial_operator" or attr2 == "convert_operator":
#                     continue
#                 if attr >= attr2:
#                     continue
#                 state['eq(%s,%s)' % (attr, attr2)] = self.tutor.state[attr] == self.tutor.state[attr2]

#         return state

#     def step(self, action):
#         self.n_steps += 1
#         try:
#             s, a, i = self.decode(action)
#             reward = self.tutor.apply_sai(s, a, i)
#             done = (s == 'done' and reward == 1.0)
#         except ValueError:
#             reward = -1
#             done = False

#         # print(s, a, i)
#         # print()
#         # print(reward)
        
#         state = self.get_rl_state()
#         # pprint(state)
#         obs = self.dv.fit_transform([state])[0]
#         info = {}

#         if self.n_steps > self.max_steps:
#             done = True

#         return obs, reward, done, info


#     def apply_rl_op(self, op, arg1, arg2):
#         if op == "copy":
#             return self.tutor.state[arg1]
#         elif op == "add":
#             return str(int(self.tutor.state[arg1]) + int(self.tutor.state[arg2]))
#         elif op == "multiply":
#             return str(int(self.tutor.state[arg1]) * int(self.tutor.state[arg2]))

#     def decode(self, action):
#         # print(action)
#         s = self.tutor.get_possible_selections()[action[0]]
#         op = self.get_rl_operators()[action[1]]
#         arg1 = self.tutor.get_possible_args()[action[2]]
#         arg2 = self.tutor.get_possible_args()[action[3]]

#         if s == "done":
#             a = "ButtonPressed"
#         else:
#             a = "UpdateField"
        
#         if s == "done":
#             v = -1
#         if s == "check_convert":
#             v = "x"
#         else:
#             v = self.apply_rl_op(op, arg1, arg2)

#         i = str(v)

#         return s, a, i

#     def reset(self):
#         self.n_steps = 0
#         self.tutor.set_random_problem()
#         state = self.get_rl_state()
#         obs = self.dv.fit_transform([state])[0]
#         return obs

#     def render(self, mode='human', close=False):
#         self.tutor.render()


if __name__ == "__main__":
    problems = [{"op" : "+", "fracs" : [("1","2"), ("1","3")]},
                {"op" : "*", "fracs" : [("1","2"), ("1","3")]}]
    # problems = [{'op': '+', 'fracs': [('11', '13'), ('13', '14')]}]
    env = FractionArithmetic(demo_annotations=["arg_foci", "how_help"],
                             check_annotations=["arg_foci"],
                             problem_types=["AD","AS","M"], n_fracs=2)



    env.make_compl_prof("gt.txt", problems)
