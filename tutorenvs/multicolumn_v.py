from random import randint
from random import choice
from pprint import pprint
import logging

import cv2  # pytype:disable=import-error
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
import numpy as np
from PIL import Image, ImageDraw
from colorama import Back, Fore
from tutorenvs.fsm import StateMachine

from tutorenvs.utils import OnlineDictVectorizer
from tutorenvs.utils import DataShopLogger
from tutorenvs.utils import StubLogger

pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)


def custom_add(a, b):
    if a == '':
        a = '0'
    if b == '':
        b = '0'
    return int(a) + int(b)

class MultiColumnAdditionSymbolic:

    def __init__(self, logger=None, n=3):
        """
        Creates a state and sets a random problem.
        """
        if logger is None:
            self.logger = DataShopLogger('MulticolumnAdditionTutor', extra_kcs=['field'])
            # self.logger = StubLogger()
        else:
            self.logger = logger

        if n < 1:
            raise Exception("n cannot be lower than 1.")
        self.n = n
        self.problem = None

        self.coords = {
            "operator" : {"x" :-110,"y" : 220 , "width" : 100, "height" : 100},
            "line" :     {"x" :0,   "y" : 325 , "width" : 5, "height" : 5},
            "done" :     {"x" :340, "y" : 430 , "width" : 100, "height" : 100},
            "hidey1" :   {"x" :self.n * 110, "y" : 0 , "width" : 100, "height" : 100},
            "hidey2" :   {"x" :0,   "y" : 110 , "width" : 100, "height" : 100},
            "hidey3" :   {"x" :0,   "y" : 220 , "width" : 100, "height" : 100},
        }

        # TODO: How important is the omission of ones_carry?
        for i in range(self.n):
            offset = (self.n - i) * 110
            self.coords.update({
                "{}_carry".format(i): {"x" :offset,   "y" : 0 , "width" : 100, "height" : 100},
                "{}_upper".format(i): {"x" :offset,   "y" : 110 , "width" : 100, "height" : 100},
                "{}_lower".format(i): {"x" :offset,   "y" : 220 , "width" : 100, "height" : 100},
                "{}_answer".format(i): {"x" :offset,   "y" : 330 , "width" : 100, "height" : 100},
            })

        self.coords.update({
            "{}_carry".format(self.n): {"x" :0,   "y" : 0 , "width" : 100, "height" : 100},
            "{}_answer".format(self.n): {"x" :0,   "y" : 330 , "width" : 100, "height" : 100},
        })

        self.logger.set_student()
        self.set_random_problem()


    def create_state_machine(self):
        carry = False
        fsm = StateMachine()
        for i in range(self.n):
            upper = self.state['{}_upper'.format(i)]
            lower = self.state['{}_lower'.format(i)]
            sum = custom_add(upper, lower)

            foci = ['{}_upper'.format(i), '{}_lower'.format(i)]
            if carry:
                sum += 1
                foci.append('{}_carry'.format(i))

            if sum >= 10:
                sai = ('{}_answer'.format(i), 'UpdateTextField',
                      {'value': str(sum % 10)})
                fsm.add_next_state(sai, foci)

                sai = ('{}_carry'.format(i+1), 'UpdateTextField',
                      {'value': '1'})
                fsm.add_next_state(sai, foci)
                carry = True
            else:
                sai = ('{}_answer'.format(i), 'UpdateTextField',
                      {'value': str(sum)})
                fsm.add_next_state(sai, foci)
                carry = False

        if carry:
            foci = ['{}_carry'.format(self.n)]
            sai = ('{}_answer'.format(self.n), 'UpdateTextField',
                    {'value': str(1)})
            fsm.add_next_state(sai, foci)

        sai = ('done', "ButtonPressed", {'value': -1})
        fsm.add_next_state(sai)

        fsm.reset()
        return fsm


    def reset(self, upper, lower, pad_zeros=False):
        """
        Sets the state to a new fraction arithmetic problem as specified by the
        provided arguments.
        """
        correct_answer = str(int(upper) + int(lower))
        self.correct_answer = [c for c in correct_answer]
        self.correct_answer.reverse()

        while len(self.correct_answer) < self.n:
            self.correct_answer.append('')

        if(pad_zeros):
            upper = upper.zfill(self.n)
            lower = lower.zfill(self.n)

        upper = upper[::-1]
        lower = lower[::-1]

        self.correct_answer = [c for c in correct_answer]
        self.correct_answer.reverse()
        
        self.num_correct_steps = 0
        self.num_incorrect_steps = 0
        self.num_hints = 0

        # TODO: How important is the omission of ones_carry?
        self.state = { 'operator': '+' }
        for i in range(self.n):
            self.state.update({
                '{}_upper'.format(i): upper[i],
                '{}_lower'.format(i): lower[i],
                '{}_answer'.format(i): '',
                '{}_carry'.format(i): ''
            })

        self.state.update({ 
            '{}_answer'.format(self.n): '',
            '{}_carry'.format(self.n): ''
        })

        self.fsm = self.create_state_machine()

    def get_possible_selections(self):
        selections = ['done']
        for i in range(self.n+1):
            selections.extend(["{}_carry".format(i), "{}_answer".format(i)])

        return selections

    def get_possible_args(self):
        args = []
        for i in range(self.n):
            args.extend([
                "{}_carry".format(i), 
                "{}_answer".format(i),
                "{}_lower".format(i),
                "{}_upper".format(i)
            ])

        args.extend([
            "{}_carry".format(self.n), 
            "{}_answer".format(self.n)
        ])
        return args

    def render(self, add_dot=None):
        img = self.get_image(add_counts=True, add_dot=add_dot)
        cv2.imshow('vecenv', np.array(img))
        cv2.waitKey(1)

    # TODO
    def get_image(self, add_counts=False, add_dot=None):
        state = {attr: " " if self.state[attr] == '' else
                self.state[attr] for attr in self.state}

        output = " %s%s%s \n  %s%s%s\n+ %s%s%s\n-----\n %s%s%s%s\n" % (
                state["thousands_carry"],
                state["hundreds_carry"],
                state["tens_carry"],
                state["upper_hundreds"],
                state["upper_tens"],
                state["upper_ones"],
                state["lower_hundreds"],
                state["lower_tens"],
                state["lower_ones"],
                state["answer_thousands"],
                state["answer_hundreds"],
                state["answer_tens"],
                state["answer_ones"],
                )

        img = Image.new('RGB', (50, 90), color="white")
        d = ImageDraw.Draw(img)
        d.text((10, 10), output, fill='black')

        # Draw input fields

        # ones
        if state['answer_ones'] == " ":
            d.rectangle(((34, 71), (38, 79)), fill=None, outline='black')
        # tens
        if state['answer_tens'] == " ":
            d.rectangle(((28, 71), (32, 79)), fill=None, outline='black')
        # hundreds
        if state['answer_hundreds'] == " ":
            d.rectangle(((22, 71), (26, 79)), fill=None, outline='black')
        # thousands
        if state['answer_thousands'] == " ":
            d.rectangle(((16, 71), (20, 79)), fill=None, outline='black')

        # ones carry
        if state['tens_carry'] == " ":
            d.rectangle(((28, 11), (32, 19)), fill=None, outline='black')
        # tens carry
        if state['hundreds_carry'] == " ":
            d.rectangle(((22, 11), (26, 19)), fill=None, outline='black')
        # hundreds carry
        if state['thousands_carry'] == " ":
            d.rectangle(((16, 11), (20, 19)), fill=None, outline='black')

        # append correct/incorrect counts
        if add_counts:
            d.text((0, 0), "h:{}".format(self.num_hints), fill=(0,0,0))
            d.text((0, 80), "-:{}".format(self.num_incorrect_steps), fill=(0,0,0))
            d.text((20, 0), "+:{}".format(self.num_correct_steps), fill=(0,0,0))

        if add_dot:
            d.ellipse((add_dot[0]-3, add_dot[1]-3, add_dot[0]+3, add_dot[1]+3),
                    fill=None, outline='blue')

        return img

    def get_state(self):
        """
        Returns the current state as a dict.
        """
        text_field_params = {'type': 'TextField', 'dom_class': 'CTATTextInput', 'offsetParent' : 'background-initial'}
        state_output = {_id:
                        {'id': _id, 'value': value,
                         # 'column': 'thousands' if 'thousands' in _id else
                         # 'hundreds' if 'hundreds' in _id else 'tens' if 'tens'
                         # in _id else 'ones',
                         # 'row': 'answer' if 'answer' in _id else
                         # 'lower' if 'lower' in _id else 'upper' if 'upper'
                         # in _id else 'carry',
                         # 'type': 'TextField',
                         **text_field_params,
                         'contentEditable': value == "",
                         # 'dom_class': 'CTATTextInput',
                         **self.coords[_id]
                         }
                        for _id, value in self.state.items()}
        hidey_field_params = {**text_field_params, "contentEditable" : False, "value" : ""}
        state_output['hidey1'] = {
            "id" : "hidey1",
            **hidey_field_params,
            **self.coords['hidey1']
        }
        state_output['hidey2'] = {
            "id" : "hidey2",
            **hidey_field_params,
            **self.coords['hidey2']
        }
        state_output['hidey3'] = {
            "id" : "hidey3",
            **hidey_field_params,
            **self.coords['hidey3']
        }
        # state_output['line'] = {
        #     'id': 'line',
        #     'type': 'Component',
        #     'dom_class': 'Line',
        #     **self.coords['line']
        # }
        state_output['done'] = {
            'id': 'done',
            'type': 'Component',
            'dom_class': 'CTATDoneButton',
            **self.coords['done']
        }

        return state_output


    def set_random_problem(self,pad_zeros=True):
        max_val = (10 ** self.n) - 1
        upper = str(randint(1,max_val))
        lower = str(randint(1,max_val))

        self.set_problem(upper, lower, pad_zeros)

    
    def set_problem(self, upper, lower, pad_zeros=True):
        upper = str(upper)
        lower = str(lower)

        print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {upper} + {lower}" )

        self.reset(upper=upper, lower=lower,pad_zeros=pad_zeros)
        self.logger.set_problem("%s_%s" % (upper, lower))
        self.problem = (upper, lower)


    def apply_sai(self, selection, action, inputs, apply_incorrects=True):
        """
        Give a SAI, it applies it. This method returns feedback (i.e., -1 or 1).
        """
        reward = self.fsm.apply(selection, action, inputs)
        
        if reward > 0:
            outcome = "CORRECT"
            self.num_correct_steps += 1
        else:
            outcome = "INCORRECT"
            self.num_incorrect_steps += 1

        self.logger.log_step(selection, action, inputs['value'], outcome, step_name=selection, kcs=[selection])

        if reward == -1.0:
            return reward

        if selection == "done":
            self.set_random_problem()

        elif(reward > 0 or apply_incorrects):
            self.state[selection] = inputs['value']

        return reward


    # TODO still need to rewrite for multi column arith
    def request_demo(self,return_foci=False):
        demo = self.get_demo(return_foci=return_foci)
        sai, foci = demo if(return_foci) else (demo, None)
        feedback_text = f"selection: {sai[0]}, action: {sai[1]}, input: {sai[2]['value']}"
        self.logger.log_hint(feedback_text, step_name=sai[0], kcs=[sai[0]])
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


class MultiColumnAdditionDigitsEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.tutor = MultiColumnAdditionSymbolic()
        n_selections = len(self.tutor.get_possible_selections())
        n_features = 110
        self.dv = OnlineDictVectorizer(n_features)
        self.observation_space = spaces.Box(low=0.0,
                high=1.0, shape=(1, n_features), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_selections, 10])
        self.n_steps = 0
        self.max_steps = 5000

    def get_rl_state(self):
        return self.tutor.state

    def step(self, action, apply_incorrects=True):
        self.n_steps += 1

        s, a, i = self.decode(action)
        # print(s, a, i)
        # print()
        reward = self.tutor.apply_sai(s, a, i, apply_incorrects=apply_incorrects)
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
        v = i['value']
        out = np.zeros(1,dtype=np.int64)
        enc_s = self.tutor.get_possible_selections().index(s)
        if(s == 'done' or s == "check_convert"):
            v = 0
        # n = len(self.tutor.get_possible_selections()) 
        out[0] = 10 * enc_s + int(v) 
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
            a = "UpdateTextField"
        
        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = action[1]

        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.n_steps = 0
        self.tutor.set_random_problem()
        # self.render()
        state = self.get_rl_state()
        obs = self.dv.fit_transform([state])[0]
        return obs

    def render(self, mode='human', close=False):
        self.tutor.render()


def int2_float_add_then_ones(x, y):
    z = float(x) + float(y)
    z = z % 10
    if z.is_integer():
        z = int(z)
    return str(z)


def int2_float_add_then_tens(x, y):
    z = float(x) + float(y)
    z = z // 10
    if z.is_integer():
        z = int(z)
    return str(z)


def int3_float_add_then_ones(x, y, w):
    z = float(x) + float(y) + float(w)
    z = z % 10
    if z.is_integer():
        z = int(z)
    return str(z)


def int3_float_add_then_tens(x, y, w):
    z = float(x) + float(y) + float(w)
    z = z // 10
    if z.is_integer():
        z = int(z)
    return str(z)


def add_tens(x, y, w):
    if w is None:
        return int2_float_add_then_tens(x, y)
    return int3_float_add_then_tens(x, y, w)


def add_ones(x, y, w):
    if w is None:
        return int2_float_add_then_ones(x, y)
    return int3_float_add_then_ones(x, y, w)


class MultiColumnAdditionOppEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.tutor = MultiColumnAdditionSymbolic()
        n_selections = len(self.tutor.get_possible_selections())
        n_features = 5000
        n_operators = len(self.get_rl_operators())
        n_args = len(self.tutor.get_possible_args())
        self.dv = OnlineDictVectorizer(n_features)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(1, n_features), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_selections, n_operators,
                                                  n_args, n_args, n_args])
        self.n_steps = 0
        self.max_steps = 100000

    def get_rl_operators(self):
        return ['copy',
                'add2-tens',
                'add2-ones',
                'add3-tens',
                'add3-ones',
                ]

    def get_rl_state(self):
        state = self.tutor.state.copy()
        for attr in self.tutor.state:
            if attr == "operator" or state[attr] == "":
                continue
            for attr2 in self.tutor.state:
                if attr2 == "operator" or state[attr2] == "":
                    continue
                if attr >= attr2:
                    continue

                ones2 = int2_float_add_then_ones(state[attr], state[attr2])
                state['add2-ones(%s,%s)' % (attr, attr2)] = ones2
                tens2 = int2_float_add_then_tens(state[attr], state[attr2])
                state['add2-tens(%s,%s)' % (attr, attr2)] = tens2

                for attr3 in self.tutor.state:
                    if attr3 == "operator" or state[attr3] == "":
                        continue
                    if attr2 >= attr3:
                        continue

                    ones3 = int3_float_add_then_ones(state[attr], state[attr2],
                                                     state[attr3])
                    state['add3-ones(%s,%s,%s)' % (attr, attr2, attr3)] = ones3
                    tens3 = int3_float_add_then_tens(state[attr], state[attr2],
                                                     state[attr3])
                    state['add3-tens(%s,%s,%s)' % (attr, attr2, attr3)] = tens3

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

        # self.tutor.render()

        # print(s, a, i)
        # print()
        # print(reward)

        state = self.get_rl_state()
        # pprint(state)
        obs = self.dv.fit_transform([state])[0]
        info = {}

        # have a max steps for a given problem.
        # When we hit that we're done regardless.
        if self.n_steps > self.max_steps:
            done = True

        return obs, reward, done, info

    def apply_rl_op(self, op, arg1, arg2, arg3):
        if op == "copy":
            return self.tutor.state[arg1]
        elif op == "add2-tens":
            return int2_float_add_then_tens(self.tutor.state[arg1],
                                            self.tutor.state[arg2])
        elif op == "add2-ones":
            return int2_float_add_then_ones(self.tutor.state[arg1],
                                            self.tutor.state[arg2])
        elif op == "add3-tens":
            return int3_float_add_then_tens(self.tutor.state[arg1],
                                            self.tutor.state[arg2],
                                            self.tutor.state[arg3])
        elif op == "add3-ones":
            return int3_float_add_then_ones(self.tutor.state[arg1],
                                            self.tutor.state[arg2],
                                            self.tutor.state[arg3])

    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]
        op = self.get_rl_operators()[action[1]]
        arg1 = self.tutor.get_possible_args()[action[2]]
        arg2 = self.tutor.get_possible_args()[action[3]]
        arg3 = self.tutor.get_possible_args()[action[3]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateTextField"

        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = self.apply_rl_op(op, arg1, arg2, arg3)

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


class MultiColumnAdditionPixelEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def get_rl_state(self):
        img = self.tutor.get_image().convert('L')
        return np.expand_dims(np.array(img), axis=2)

    def __init__(self):
        self.tutor = MultiColumnAdditionSymbolic()
        n_selections = len(self.tutor.get_possible_selections())

        print('shape = ', self.get_rl_state().shape)

        self.observation_space = spaces.Box(low=0,
                high=255, shape=self.get_rl_state().shape, dtype=np.uint8)
        self.action_space = spaces.MultiDiscrete([n_selections, 10])

    def step(self, action):
        s, a, i = self.decode(action)
        # print(s, a, i)
        # print()
        reward = self.tutor.apply_sai(s, a, i)
        # print(reward)
        
        obs = self.get_rl_state()
        # pprint(state)
        done = (s == 'done' and reward == 1.0)
        info = {}

        return obs, reward, done, info

    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateTextField"
        
        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = action[1]

        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.tutor.set_random_problem()
        obs = self.get_rl_state()
        return obs

    def render(self, mode='human', close=False):
        if mode == "rgb_array":
            return np.array(self.tutor.get_image(add_counts=True))

        elif mode == "human":
            self.tutor.render()

class MultiColumnAdditionPerceptEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.targets = ['answer_ones', 'tens_carry', 'answer_tens',
                'hundreds_carry', 'answer_hundreds', 'thousands_carry',
                'answer_thousands']
        self.target_xy = [
                (36, 75),
                (30, 15),
                (30, 75),
                (24, 15),
                (24, 75),
                (18, 15),
                (18, 75)
                ]

        self.current_target = 0

        self.set_xy()

        self.tutor = MultiColumnAdditionSymbolic()
        n_selections = len(self.tutor.get_possible_selections())

        print('shape = ', self.get_rl_state().shape)

        self.observation_space = spaces.Box(low=0,
                high=255, shape=self.get_rl_state().shape, dtype=np.uint8)
        # self.action_space = spaces.MultiDiscrete([n_selections, 10])
        self.action_space = spaces.Discrete(12)

    def set_xy(self):
        self.x, self.y = self.target_xy[self.current_target]

    def get_rl_state(self):
        img = self.tutor.get_image().convert('L')
        x_multiplier = 0.75 
        y_multiplier = 1.5
        x = round(self.x - (25 * x_multiplier))
        y = round(self.y - (45 * y_multiplier))

        translate = img.transform((round(img.size[0]*x_multiplier),
            round(img.size[1]*y_multiplier)), Image.AFFINE, (1, 0, x, 0, 1, y), fillcolor='white')

        # Pretty output
        cv2.imshow('translated', np.array(translate))
        cv2.waitKey(1)
        self.render()

        return np.expand_dims(np.array(translate), axis=2)

    def step(self, action):
        s = None
        reward = -1

        # if action == 0:
        #     # left
        #     self.x -= 5
        # elif action == 1:
        #     # right
        #     self.x += 5
        # elif action == 2:
        #     # up
        #     self.y += 5
        # elif action == 3:
        #     # down
        #     self.y -= 5
        if action == 0:
            self.current_target = (self.current_target + 1) % len(self.targets)
            self.set_xy()

        elif action == 1:
            s = "done"
            a = "ButtonPressed"
            i = -1
        else:

            # answer fields
            if self.x >= 34 and self.y >= 71 and self.x <= 38 and self.y <=79:
                s = "answer_ones"
            elif self.x >= 28 and self.y >= 71 and self.x <= 32 and self.y <=79:
                s = "answer_tens"
            elif self.x >= 22 and self.y >= 71 and self.x <= 26 and self.y <=79:
                s = "answer_hundreds"
            elif self.x >= 16 and self.y >= 71 and self.x <= 20 and self.y <=79:
                s = "answer_thousands"

            # carry fields
            elif self.x >= 28 and self.y >= 11 and self.x <= 32 and self.y <=19:
                s = "tens_carry"
            elif self.x >= 22 and self.y >= 11 and self.x <= 26 and self.y <=19:
                s = "hundreds_carry"
            elif self.x >= 16 and self.y >= 11 and self.x <= 20 and self.y <=19:
                s = "thousands_carry"

            a = 'UpdateTextField'
            i = {'value': str(action - 2)}

        if s != None:
            reward = self.tutor.apply_sai(s, a, i)

        # code to skip completed fields
        # skipper = 0
        # original_target = self.current_target
        # while self.tutor.state[self.targets[self.current_target]] != '':
        #     self.current_target = (self.current_target + 1) % len(self.targets)
        #     skipper += 1
        #     if skipper > 7:
        #         self.current_target = original_target
        #         break
        # self.set_xy()

        self.x = min(max(self.x, 0), 50)
        self.y = min(max(self.y, 0), 90)

        obs = self.get_rl_state()
        done = (s == 'done' and reward == 1.0)
        info = {}

        # self.render()

        return obs, reward, done, info

    def decode(self, action):
        # print(action)
        s = self.tutor.get_possible_selections()[action[0]]

        if s == "done":
            a = "ButtonPressed"
        else:
            a = "UpdateTextField"
        
        if s == "done":
            v = -1
        if s == "check_convert":
            v = "x"
        else:
            v = action[1]

        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.tutor.set_random_problem()
        obs = self.get_rl_state()
        return obs

    def render(self, mode='human', close=False):
        if mode == "rgb_array":
            return np.array(self.tutor.get_image(add_counts=True, add_dot=(self.x, self.y)))

        elif mode == "human":
            self.tutor.render(add_dot=(self.x, self.y))
