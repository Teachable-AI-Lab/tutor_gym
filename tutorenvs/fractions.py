from random import randint
from random import choice
from pprint import pprint
import logging


import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
from tutorenvs.utils import OnlineDictVectorizer
import numpy as np

from tutorenvs.utils import DataShopLogger
from tutorenvs.utils import StubLogger

pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)

class FractionArithSymbolic:

    def __init__(self, logger=None):
        """
        Creates a state and sets a random problem.
        """
        if logger is None:
            self.logger = DataShopLogger('FractionsTutor', extra_kcs=['field'])
            # self.logger = StubLogger()
        else:
            self.logger = logger
        self.logger.set_student()
        self.set_random_problem()
        # self.reset("", "", "", "", "")

    def reset(self, num1, denom1, operator, num2, denom2):
        """
        Sets the state to a new fraction arithmetic problem as specified by the
        provided arguments.
        """
        self.steps = 0
        self.num_correct_steps = 0
        self.num_incorrect_steps = 0
        self.num_hints = 0

        self.state = {
            'initial_num_left': num1,
            'initial_denom_left': denom1,
            'initial_operator': operator,
            'initial_num_right': num2,
            'initial_denom_right': denom2,
            'check_convert': '',
            'convert_num_left': '',
            'convert_denom_left': '',
            'convert_operator': operator,
            'convert_num_right': '',
            'convert_denom_right': '',
            'answer_num': '',
            'answer_denom': '',
        }

    def get_possible_selections(self):
        return ['check_convert',
                'convert_num_left',
                'convert_denom_left',
                'convert_num_right',
                'convert_denom_right',
                'answer_num',
                'answer_denom',
                'done']

    def get_possible_args(self):
        return ['initial_num_left',
                'initial_denom_left',
                # 'initial_operator',
                'initial_num_right',
                'initial_denom_right',
                'convert_num_left',
                'convert_denom_left',
                'convert_num_right',
                'convert_denom_right',
                'answer_num',
                'answer_denom'
                ]

    def render(self, add_dot=None):
        import cv2  # pytype:disable=import-error
        img = self.get_image(add_counts=True, add_dot=add_dot)
        cv2.imshow('vecenv', np.array(img))
        cv2.waitKey(1)

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
                         'to_right': ''
                         }
                        for attr in self.state}
        state_output['done'] = {
            'id': 'done',
            'type': 'Component',
            'dom_class': 'CTATDoneButton',
            'above': '',
            'below': '',
            'to_left': '',
            'to_right': ''
        }

        return state_output

    def set_random_problem(self):
        num1 = str(randint(1, 15))
        num2 = str(randint(1, 15))
        denom1 = str(randint(2, 15))
        denom2 = str(randint(2, 15))
        operator = choice(['+', '*'])

        self.reset(num1, denom1, operator, num2, denom2)
        self.logger.set_problem("%s_%s_%s_%s_%s" % (num1, denom1, operator,
                                                    num2, denom2))

        if operator == "+" and denom1 == denom2:
            self.ptype = 'AS'
        if operator == "+" and denom1 != denom2:
            self.ptype = 'AD'
        else:
            self.ptype = 'M'

    def apply_sai(self, selection, action, inputs):
        """
        Give a SAI, it applies it. This method returns feedback
        (i.e., -1 or 1).
        """
        self.steps += 1
        reward = self.evaluate_sai(selection, action, inputs)

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
            # print("DONE! Only took %i steps." % self.steps)
            # self.render()
            # pprint(self.state)
            self.set_random_problem()

        else:
            self.state[selection] = inputs['value']


        return reward

    def evaluate_sai(self, selection, action, inputs):
        """
        Given a SAI, returns whether it is correct or incorrect.
        """
        # done step
        if selection == "done":

            if action != "ButtonPressed":
                return -1.0

            if self.state['answer_num'] != "" and self.state['answer_denom'] != "":
                return 1.0
            else:
                return -1.0

        # we can only edit selections that are editable
        if self.state[selection] != "":
            return -1.0

        if (self.state['initial_operator'] == '+' and
                self.state['initial_denom_left'] == self.state['initial_denom_right']):
            # add same denoms
            if (selection == 'answer_num' and (inputs['value'] ==
                                               str(int(self.state['initial_num_left']) +
                                                int(self.state['initial_num_right'])))):
                return 1.0

            if (selection == 'answer_denom' and inputs['value'] ==
                    self.state['initial_denom_left']):
                return 1.0

            return -1.0

        if (self.state['initial_operator'] == "+" and
                self.state['initial_denom_left'] != self.state['initial_denom_right']):
            # add, different denoms
            if selection == "check_convert":
                return 1.0

            if (selection == "convert_num_left" and
                    self.state['convert_denom_left'] != "" and
                    inputs['value'] == str(int(self.state['initial_num_left']) *
                                        int(self.state['initial_denom_right']))):
                return 1.0

            if (selection == "convert_denom_left" and
                    self.state['check_convert'] != "" and
                    inputs['value'] == str(int(self.state['initial_denom_left']) *
                                        int(self.state['initial_denom_right']))):
                return 1.0

            if (selection == "convert_num_right" and
                    self.state['convert_denom_right'] != "" and
                    inputs['value'] == str(int(self.state['initial_num_right']) *
                                        int(self.state['initial_denom_left']))):
                return 1.0

            if (selection == "convert_denom_right" and
                    self.state['convert_denom_left'] != "" and
                    inputs['value'] == str(int(self.state['initial_denom_left']) *
                                        int(self.state['initial_denom_right']))):
                return 1.0

            if (selection == 'answer_num' and
                    self.state['convert_num_left'] != "" and
                    self.state['convert_num_right'] != "" and
                    (inputs['value'] == str(int(self.state['convert_num_left']) +
                                         int(self.state['convert_num_right'])))):
                return 1.0

            if (selection == 'answer_denom' and
                    self.state['convert_num_left'] != "" and
                    self.state['convert_num_right'] != "" and
                    inputs['value'] == self.state['convert_denom_right']):
                return 1.0

            return -1.0

        if (self.state['initial_operator'] == "*"):
            # multiply
            if (selection == 'answer_num' and (inputs['value'] ==
                                               str(int(self.state['initial_num_left']) *
                                                int(self.state['initial_num_right'])))):
                return 1.0

            if (selection == 'answer_denom' and (inputs['value'] ==
                                                 str(int(self.state['initial_denom_left']) *
                                                  int(self.state['initial_denom_right'])))):
                return 1.0

            return -1.0

        raise Exception("evaluate_sai logic missing")

    def request_demo(self):
        demo = self.get_demo()
        feedback_text = "selection: %s, action: %s, input: %s" % (demo[0],
                demo[1], demo[2]['value'])
        self.logger.log_hint(feedback_text, step_name=self.ptype + '_' +
                             demo[0], kcs=[self.ptype + '_' + demo[0]])
        self.num_hints += 1

        return demo

    def get_demo(self):
        """
        Returns a correct next-step SAI
        """
        if (self.state['initial_operator'] == '+' and
                self.state['initial_denom_left'] == self.state['initial_denom_right']):
            if self.state['answer_num'] == "":
                return ('answer_num', "UpdateField",
                        {'value': str(int(self.state['initial_num_left']) +
                                      int(self.state['initial_num_right']))})

            if self.state['answer_denom'] == "":
                return ('answer_denom', "UpdateField",
                        {'value': self.state['initial_denom_left']})

            return ('done', "ButtonPressed", {'value': -1})

        if (self.state['initial_operator'] == "+" and
                self.state['initial_denom_left'] != self.state['initial_denom_right']):
            
            if self.state['check_convert'] == "":
                return ('check_convert', 'UpdateField', {"value": 'x'})

            if self.state['convert_denom_left'] == "":
                return ('convert_denom_left', "UpdateField",
                        {'value': str(int(self.state['initial_denom_left']) *
                                      int(self.state['initial_denom_right']))})

            if self.state['convert_num_left'] == "":
                return ('convert_num_left', "UpdateField",
                        {'value': str(int(self.state['initial_num_left']) *
                                      int(self.state['initial_denom_right']))})

            if self.state['convert_denom_right'] == "":
                return ('convert_denom_right', "UpdateField",
                        {'value': str(int(self.state['initial_denom_left']) *
                                      int(self.state['initial_denom_right']))})

            if self.state['convert_num_right'] == "":
                return ('convert_num_right', "UpdateField",
                        {'value': str(int(self.state['initial_denom_left']) *
                                      int(self.state['initial_num_right']))})

            if self.state['answer_num'] == "":
                return ('answer_num', "UpdateField",
                        {'value': str(int(self.state['convert_num_left']) +
                                      int(self.state['convert_num_right']))})

            if self.state['answer_denom'] == "":
                return ('answer_denom', "UpdateField",
                        {'value': self.state['convert_denom_right']})

            return ('done', "ButtonPressed", {'value': -1})

        if (self.state['initial_operator'] == "*"):
            if self.state['answer_num'] == "":
                return ('answer_num', "UpdateField",
                        {'value': str(int(self.state['initial_num_left']) *
                                      int(self.state['initial_num_right']))})

            if self.state['answer_denom'] == "":
                return ('answer_denom', "UpdateField",
                        {'value': str(int(self.state['initial_denom_left']) *
                                      int(self.state['initial_denom_right']))})

            return ('done', "ButtonPressed", {'value': -1})

        raise Exception("request demo - logic missing")


class FractionArithNumberEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, logger=None):
        self.tutor = FractionArithSymbolic(logger=logger)
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
