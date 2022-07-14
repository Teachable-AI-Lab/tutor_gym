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

from tutorenvs.utils import DataShopLogger
from tutorenvs.utils import StubLogger
from tutorenvs.fsm import StateMachine

pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)


def same_denoms(denoms):
    return len(set(denoms)) == 1


class FractionArithSymbolic:

    def __init__(self, logger=None, n=2):
        """
        Creates a state and sets a random problem.
        """
        if logger is None:
            self.logger = DataShopLogger('FractionsTutor', extra_kcs=['field'])
            # self.logger = StubLogger()
        else:
            self.logger = logger

        if n < 2:
            raise Exception("n cannot be lower than 2.")
        self.n = n
        self.logger.set_student()
        self.set_random_problem()

    def create_state_machine(self):
        fsm = StateMachine()

        init_nums = [int(self.state['initial_num_{}'.format(i)]) for i in range(self.n)]
        init_denoms = [int(self.state['initial_denom_{}'.format(i)]) for i in range(self.n)]
        sd = same_denoms(init_denoms)

        # TODO: Make the order insignificant?
        if self.state['initial_operator'] == "*":
            # Multiplication
            foci = ["initial_denom_{}".format(i) for i in range(self.n)]
            sai = ('answer_denom', 'UpdateField', 
                   {'value': str(reduce(operator.mul, init_denoms))})
            fsm.add_next_state(sai, foci)

            foci = [*["initial_num_{}".format(i) for i in range(self.n)],
                    *["initial_denom_{}".format(i) for i in range(self.n)]]
            sai = ('answer_num', 'UpdateField', 
                   {'value': str(reduce(operator.mul, init_nums))})
            fsm.add_next_state(sai, foci)
        elif sd:
            # Addition Same
            foci = ["initial_denom_{}".format(i) for i in range(self.n)]
            sai = ('answer_denom', 'UpdateField', 
                   {'value': str(self.state['initial_denom_0'])})
            fsm.add_next_state(sai, foci)

            foci = [*["initial_num_{}".format(i) for i in range(self.n)],
                    *["initial_denom_{}".format(i) for i in range(self.n)]]
            sai = ('answer_num', 'UpdateField', 
                   {'value': str(sum(init_nums))})
            fsm.add_next_state(sai, foci)
        else:
            # Addition Different
            foci = []#["initial_denom_{}".format(i) for i in range(self.n)]
            sai = ('check_convert', 'UpdateField', {'value': 'x'})
            fsm.add_next_state(sai, foci)

            
            convert_denom = reduce(operator.mul, init_denoms)
            for i in range(self.n):
                if(i == 0):
                    foci = ["initial_denom_{}".format(i) for i in range(self.n)]
                else:
                    foci = [f"convert_denom_{i-1}"]
                sai = ('convert_denom_{}'.format(i), 'UpdateField', {'value': str(convert_denom)})
                fsm.add_next_state(sai, foci)

            convert_nums = []
            for i in range(self.n):
                # foci = [*["initial_denom_{}".format(j) for j in range(self.n)],
                #         "initial_num_{}".format(i)]
                # foci.remove("initial_denom_{}".format(i))

                foci = [f"convert_denom_{i}", f"initial_num_{i}", f"initial_denom_{i}"]

                convert_num = int((convert_denom * init_nums[i]) / init_denoms[i])
                sai = ('convert_num_{}'.format(i), 'UpdateField', {'value': str(convert_num)})
                fsm.add_next_state(sai, foci)
                convert_nums.append(convert_num)

            foci = ["convert_num_{}".format(i) for i in range(self.n)]
            sai = ('answer_num', 'UpdateField', {'value': str(sum(convert_nums))})
            fsm.add_next_state(sai, foci)

            foci = [f"convert_denom_{self.n-1}"]
            sai = ('answer_denom', 'UpdateField', {'value': str(convert_denom)})
            fsm.add_next_state(sai, foci)

        foci = ['answer_num', 'answer_denom']
        sai = ('done', "ButtonPressed", {'value': -1})
        fsm.add_next_state(sai, foci)

        fsm.reset()
        return fsm


    def reset(self, nums, denoms, operator):
        """
        Sets the state to a new fraction arithmetic problem as specified by the
        provided arguments.
        """
        self.steps = 0
        self.num_correct_steps = 0
        self.num_incorrect_steps = 0
        self.num_hints = 0

        self.state = {'check_convert': '',
                      'answer_num': '',
                      'answer_denom': '',
                      'initial_operator': operator,
                      'convert_operator': operator}
        
        for i in range(self.n):
            self.state.update({'initial_num_{}'.format(i): str(nums[i]),
                               'initial_denom_{}'.format(i): str(denoms[i]),
                               'convert_num_{}'.format(i): '',
                               'convert_denom_{}'.format(i): ''})

        self.fsm = self.create_state_machine()

    def get_possible_selections(self):
        sels = ['check_convert',
                'answer_num',
                'answer_denom',
                'done']
        for i in range(self.n):
            sels.extend(['convert_num_{}'.format(i),
                         'convert_denom_{}'.format(i)])
        return sels

    def get_possible_args(self):
        args = ['check_convert',
                'answer_num',
                'answer_denom']
        for i in range(self.n):
            args.extend(['initial_num_{}'.format(i),
                         'initial_denom_{}'.format(i),
                         'convert_num_{}'.format(i),
                         'convert_denom_{}'.format(i)])
        return args

    # TODO
    def render(self, add_dot=None):
        img = self.get_image(add_counts=True, add_dot=add_dot)
        cv2.imshow('vecenv', np.array(img))
        cv2.waitKey(1)

    # TODO
    def get_image(self, add_counts=False, add_dot=None):
        output = "{:>3}    {:>3}\n---- {} ---- =\n{:>3}    {:>3}\n\nConvert? | {} |\n\n{:>3}    {:>3}    {:>3}\n---- {} ---- = ----\n{:>3}    {:>3}    {:>3}\n".format(self.state['initial_num_left'],
                self.state['initial_num_right'],
                self.state['initial_operator'],
                self.state['initial_denom_left'],
                self.state['initial_denom_right'],
                self.state['check_convert'],
                self.state['convert_num_left'],
                self.state['convert_num_right'],
                self.state['answer_num'],
                self.state['convert_operator'],
                self.state['convert_denom_left'],
                self.state['convert_denom_right'],
                self.state['answer_denom'])

        img = Image.new('RGB', (125, 150), color="white")
        d = ImageDraw.Draw(img)
        d.text((10, 10), output, fill='black')

        # Draw input fields

        # ones
        # if state['answer_ones'] == " ":
        #     d.rectangle(((34, 71), (38, 79)), fill=None, outline='black')

        # append correct/incorrect counts
        if add_counts:
            d.text((95, 0), "h:{}".format(self.num_hints), fill=(0,0,0))
            d.text((95, 10), "-:{}".format(self.num_incorrect_steps), fill=(0,0,0))
            d.text((95, 20), "+:{}".format(self.num_correct_steps), fill=(0,0,0))

        # for eyes :)
        # if add_dot:
        #     d.ellipse((add_dot[0]-3, add_dot[1]-3, add_dot[0]+3, add_dot[1]+3),
        #             fill=None, outline='blue')

        return img

    def _get_coord(self, name):
        if name == "answer_num":
            x = (self.n * 100) + 100
            y = 200
        elif name == "answer_denom":
            x = (self.n * 100) + 100
            y = 300
        elif name == "initial_operator":
            # x = (self.n * 100)
            # y = 50
            x = 0
            y = 700
        elif name == "convert_operator":
            # x = (self.n * 100)
            # y = 150
            x = 0
            y = 600
        elif name == "check_convert":
            # x = (self.n * 100) + 200
            x = 0
            y = 500
        elif name == "done":
            x = 0
            y = 300
        else:
            t, n, idx = name.split("_")
            c1 = 0 if t == "initial" else 200
            c2 = 0 if n == "num" else 100
            y = c1 + c2
            x = int(idx) * 100

        return {"x": x,
                "y": y,
                "width": 100,
                "height": 100}

    def get_state(self):
        """
        Returns the current state as a dict.
        """
        state_output = {attr:
                        {'id': attr, 'value': self.state[attr],
                         'type': 'TextField',
                         'contentEditable': self.state[attr] == "",
                         'dom_class': 'CTATTable--cell',
                         'above': '',
                         'below': '',
                         'to_left': '',
                         'to_right': '',
                         **self._get_coord(attr)
                        }
                        for attr in self.state}
        state_output['done'] = {
            'id': 'done',
            'type': 'Component',
            'dom_class': 'CTATDoneButton',
            'above': '',
            'below': '',
            'to_left': '',
            'to_right': '',
            **self._get_coord('done')
        }
        return state_output

    def set_random_problem(self):
        ok = False
        # typ = choice(["AD", "AS", "M"])
        # typ = choice(["AD", "AS", "M"])
        # if(typ == "AD"):
        while(not ok):
            nums = [str(randint(1, 15)) for _ in range(self.n)]
            denoms = [str(randint(2, 15)) for _ in range(self.n)]
            ok = (not any(np.array(nums)==np.array(denoms))) and (len(set(denoms)) > 1)
        operator = choice(['+', '*'])
        # else:
        #     pass
        self.set_problem(nums, denoms, operator)

        print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {'+'.join([f'({n}/{v})' for n,v in zip(nums,denoms)])}" )

    def set_problem(self, nums, denoms, operator):
        self.reset(nums, denoms, operator)
        problem_name = "{}_{}".format(nums[0], denoms[0])
        for n, d in zip(nums[1:], denoms[1:]):
            problem_name += "{}_{}_{}".format(operator, n, d)

        self.logger.set_problem(problem_name)

        sd = same_denoms(denoms) == 1
        if operator == "+" and sd:
            self.ptype = 'AS'
        if operator == "+" and not sd == 1:
            self.ptype = 'AD'
        else:
            self.ptype = 'M'

    def apply_sai(self, selection, action, inputs):
        """
        Give a SAI, it applies it. This method returns feedback
        (i.e., -1 or 1).
        """
        self.steps += 1
        reward = self.fsm.apply(selection, action, inputs)

        if reward > 0:
            outcome = "CORRECT"
            self.num_correct_steps += 1
        else:
            outcome = "INCORRECT"
            self.num_incorrect_steps += 1

        self.logger.log_step(selection, action, inputs['value'], outcome,
                             step_name=self.ptype + '_' + selection,
                             kcs=[self.ptype + '_' + selection])

        # Render output?
        # self.render()

        if reward == -1.0:
            return reward

        if selection == "done":
            self.set_random_problem()
        elif reward > 0:
            self.state[selection] = inputs['value']

        return reward

    def request_demo(self, return_foci=False):
        demo = self.get_demo(return_foci)
        sai, foci = demo if(return_foci) else (demo, None)
        feedback_text = "selection: %s, action: %s, input: %s" % (sai[0],
                         sai[1], sai[2]['value'])
        self.logger.log_hint(feedback_text, step_name=self.ptype + '_' +
                             sai[0], kcs=[self.ptype + '_' + sai[0]])
        self.num_hints += 1
        return demo

    def get_demo(self, return_foci=False):
        """
        Returns a correct next-step SAI
        """
        sai = self.fsm.cur_state.sai
        foci = self.fsm.cur_state.foci
        if(return_foci):
            return sai, foci
        else:
            return sai


class FractionArithNumberEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.tutor = FractionArithSymbolic()
        n_selections = len(self.tutor.get_possible_selections())
        n_features = 900
        self.dv = OnlineDictVectorizer(n_features)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(1, n_features), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_selections, 450])
        self.n_steps = 0
        self.max_steps = 100000

    def step(self, action):
        self.n_steps += 1

        s, a, i = self.decode(action)
        # print("STEP", s, a, i)
        # print()
        reward = self.tutor.apply_sai(s, a, i)
        # self.render()
        # print(reward)
        state = self.tutor.state
        # pprint(state)
        obs = self.dv.fit_transform([state])[0]
        done = (s == 'done' and reward == 1.0)

        # have a max steps for a given problem.
        # When we hit that we're done regardless.
        if self.n_steps > self.max_steps:
            done = True

        info = {}

        return obs, reward, done, info

    def encode(self, sai):
        s,a,i = sai
        
        out = np.zeros(1,dtype=np.int64)
        enc_s = self.tutor.get_possible_selections().index(s)
        if(s == 'done' or s == "check_convert"):
            v = 0
        else:
            v = int(i['value']) - 1
        # n = len(self.tutor.get_possible_selections()) 
        out[0] = 450 * enc_s + int(v) 
        return out

    def request_demo_encoded(self):
        action = self.tutor.request_demo() 
        # print("DEMO ACTION:", action)
        return self.encode(action)


    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateField"

        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = action[1] + 1

        i = {'value': str(v)}
        # print(s,a,i)
        return s, a, i

    def reset(self):
        self.n_steps = 0
        self.tutor.set_random_problem()
        # self.render()
        state = self.tutor.state
        obs = self.dv.fit_transform([state])[0]
        return obs

    def render(self, mode='human', close=False):
        self.tutor.render()


class FractionArithDigitsEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def get_rl_state(self):
        # self.state = {
        #     'initial_num_left': num1,
        #     'initial_denom_left': denom1,
        #     'initial_operator': operator,
        #     'initial_num_right': num2,
        #     'initial_denom_right': denom2,
        #     'check_convert': '',
        #     'convert_num_left': '',
        #     'convert_denom_left': '',
        #     'convert_operator': operator,
        #     'convert_num_right': '',
        #     'convert_denom_right': '',
        #     'answer_num': '',
        #     'answer_denom': '',
        # }

        state = {}
        for attr in self.tutor.state:
            if attr == "initial_operator" or attr == "convert_operator":
                state[attr] = self.tutor.state[attr]
                continue

            state[attr + "[0]"] = ""
            state[attr + "[1]"] = ""
            state[attr + "[2]"] = ""

            if self.tutor.state[attr] != "":
                l = len(self.tutor.state[attr])

                if l > 2:
                    state[attr + "[0]"] = self.tutor.state[attr][-3]
                if l > 1:
                    state[attr + "[1]"] = self.tutor.state[attr][-2]

                state[attr + "[2]"] = self.tutor.state[attr][-1]

            # print(self.tutor.state[attr])
            # pprint(state)

        return state

    def __init__(self):
        self.tutor = FractionArithSymbolic()
        n_selections = len(self.tutor.get_possible_selections())
        n_features = 10000
        self.feature_hasher = FeatureHasher(n_features=n_features)

        self.observation_space = spaces.Box(low=0.0,
                high=1.0, shape=(1, n_features), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_selections, 10, 10, 10])

    def step(self, action):
        s, a, i = self.decode(action)
        # print(s, a, i)
        # print()
        reward = self.tutor.apply_sai(s, a, i)
        # print(reward)
        
        state = self.get_rl_state()
        # pprint(state)
        obs = self.feature_hasher.transform([state])[0].toarray()
        done = (s == 'done' and reward == 1.0)
        info = {}

        return obs, reward, done, info

    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateField"
        
        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = action[1]
            v += 10 * action[2]
            v += 100 * action[3]
        # if action[4]:
        #     v *= -1
        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.tutor.set_random_problem()
        state = self.get_rl_state()
        obs = self.feature_hasher.transform([state])[0].toarray()
        return obs

    def render(self, mode='human', close=False):
        self.tutor.render()


class FractionArithOppEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.tutor = FractionArithSymbolic()
        n_selections = len(self.tutor.get_possible_selections())
        n_features = 2000
        n_operators = len(self.get_rl_operators())
        n_args = len(self.tutor.get_possible_args())
        self.dv = OnlineDictVectorizer(n_features)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(1, n_features), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_selections, n_operators,
            n_args, n_args])
        self.n_steps = 0
        self.max_steps = 100000


    def get_rl_operators(self):
        return ['copy',
                'add',
                'multiply']

    def get_rl_state(self):
        state = self.tutor.state.copy()
        for attr in self.tutor.state:
            for attr2 in self.tutor.state:
                if attr == "initial_operator" or attr == "convert_operator":
                    continue
                if attr2 == "initial_operator" or attr2 == "convert_operator":
                    continue
                if attr >= attr2:
                    continue
                state['eq(%s,%s)' % (attr, attr2)] = self.tutor.state[attr] == self.tutor.state[attr2]

        return state

    def step(self, action):
        self.n_steps += 1
        try:
            s, a, i = self.decode(action)
            reward = self.tutor.apply_sai(s, a, i)
            done = (s == 'done' and reward == 1.0)
        except ValueError:
            reward = -1
            done = False

        # print(s, a, i)
        # print()
        # print(reward)
        
        state = self.get_rl_state()
        # pprint(state)
        obs = self.dv.fit_transform([state])[0]
        info = {}

        if self.n_steps > self.max_steps:
            done = True

        return obs, reward, done, info


    def apply_rl_op(self, op, arg1, arg2):
        if op == "copy":
            return self.tutor.state[arg1]
        elif op == "add":
            return str(int(self.tutor.state[arg1]) + int(self.tutor.state[arg2]))
        elif op == "multiply":
            return str(int(self.tutor.state[arg1]) * int(self.tutor.state[arg2]))

    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]
        op = self.get_rl_operators()[action[1]]
        arg1 = self.tutor.get_possible_args()[action[2]]
        arg2 = self.tutor.get_possible_args()[action[3]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateField"
        
        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = self.apply_rl_op(op, arg1, arg2)

        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.n_steps = 0
        self.tutor.set_random_problem()
        state = self.get_rl_state()
        obs = self.dv.fit_transform([state])[0]
        return obs

    def render(self, mode='human', close=False):
        self.tutor.render()
