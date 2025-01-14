from typing import Union
from typing import Callable

import os
import time
import uuid
from datetime import datetime
import logging

import gym
from gym import spaces
import numpy as np

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


def linear_schedule(
        initial_value: Union[float, str]) -> Callable[[float], float]:
    """
    Linear learning rate schedule.

    :param initial_value: (float or str)
    :return: (function)
    """
    if isinstance(initial_value, str):
        initial_value = float(initial_value)

    def func(progress_remaining: float) -> float:
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress_remaining: (float)
        :return: (float)
        """
        return progress_remaining * initial_value

    return func


def compare(a, b):
    if type(a) != type(b):
        print("[ERR] Type is not the same.")
        return False

    same = True
    if type(a) == dict:
        if len(a) != len(b):
            print("[ERR] Size is not the same.")
            return False

        for name in a:
            if name not in b:
                print("[ERR] {} is not in b".format(name))
                return False
            same = same and compare(a[name], b[name])
        return same

    if type(a) == list:
        if len(a) != len(b):
            print("[ERR] Size is not the same.")
            return False

        for x, y in zip(a, b):
            same = same and compare(x, y)
        return same

    if a != b:
        print("[ERR] {} does not equal {}".format(a, b))
        return False
    return True


class StubLogger():
    def __init__(self):
        log.info("StubLogger Created")
        pass

    def set_student(self, student_id=None):
        pass

    def set_problem(self, problem_name=None):
        pass

    def log_hint(self, feedback_text="", step_name=None, kcs=None):
        pass

    def log_step(self,
                 selection="",
                 action="",
                 inp="",
                 outcome="",
                 step_name=None,
                 kcs=None):
        pass


class DataShopLogger():
    def __init__(self, domain="tutorenv", extra_kcs=None, output_dir="log"):
        log.info("DataShop Logger Created")
        # Create log file
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        self.filename = f"{output_dir}/{domain}_{time.strftime('%Y-%m-%d-%H-%M-%S')}.txt"

        headers = [
            'Anon Student Id', 'Session Id', 'Transaction Id', 'Time',
            'Time Zone', 'Student Response Type', 'Tutor Response Type',
            'Level (Domain)', 'Problem Name', 'Problem Start Time',
            'Step Name', 'Selection', 'Action', 'Input', 'Feedback Text',
            'Outcome', 'CF (Problem Context)', 'KC (Single-KC)',
        ]

        if extra_kcs is not None:
            for kc in extra_kcs:
                headers.append('KC ({})'.format(kc))

        with open(self.filename, 'a+') as fout:
            fout.write("\t".join(headers) + "\n")

        self.time = datetime.now().timestamp()

        self.student_id = None
        self.session_id = None
        self.level_domain = domain
        self.timezone = "UTC"

    def set_student(self, student_id=None):
        if student_id is None:
            student_id = uuid.uuid4()
        self.student_id = student_id
        self.session_id = uuid.uuid4()

    def set_problem(self, problem_name=None):
        if problem_name is None:
            problem_name = uuid.uuid4()
        self.problem_name = problem_name
        self.time += 1
        self.problem_start = datetime.fromtimestamp(
            self.time).strftime('%m/%d/%Y %H:%M:%S')
        self.step_count = 1

    def log_hint(self, feedback_text, step_name=None, kcs=None):
        if self.student_id is None:
            raise Exception("No student ID")
        if self.problem_name is None:
            raise Exception("No problem name")

        transaction_id = uuid.uuid4()
        self.time += 1
        time = datetime.fromtimestamp(self.time).strftime('%m/%d/%Y %H:%M:%S')
        student_response = ""
        tutor_response = "HINT_MSG"
        self.step_count += 1
        selection = ""
        action = ""
        inp = ""
        outcome = "HINT"

        if step_name is None:
            step_name = self.step_count

        datum = [
            self.student_id,
            self.session_id,
            transaction_id,
            time,
            self.timezone,
            student_response,
            tutor_response,
            self.level_domain,
            self.problem_name,
            self.problem_start,
            # self.step_count,
            step_name,
            selection,
            action,
            inp,
            feedback_text,
            outcome,
            "",
            "Single-KC"
        ]

        if kcs is not None:
            for kc in kcs:
                datum.append(kc)

        with open(self.filename, 'a+') as fout:
            fout.write("\t".join(str(v) for v in datum) + "\n")

    def log_step(self,
                 selection,
                 action,
                 inp,
                 outcome,
                 step_name=None,
                 kcs=None):
        if self.student_id is None:
            raise Exception("No student ID")
        if self.problem_name is None:
            raise Exception("No problem name")

        transaction_id = uuid.uuid4()
        self.time += 1
        time = datetime.fromtimestamp(self.time).strftime('%m/%d/%Y %H:%M:%S')
        student_response = "ATTEMPT"
        tutor_response = "HINT_MSG"
        self.step_count += 1
        feedback_text = ""

        if step_name is None:
            step_name = self.step_count

        datum = [
            self.student_id, self.session_id, transaction_id, time,
            self.timezone, student_response, tutor_response, self.level_domain,
            self.problem_name, self.problem_start, step_name, selection,
            action, inp, feedback_text, outcome, "", "Single-KC"
        ]

        if kcs is not None:
            for kc in kcs:
                datum.append(kc)

        with open(self.filename, 'a+') as fout:
            fout.write("\t".join(str(v) for v in datum) + "\n")


class MultiDiscreteToDiscreteWrapper(gym.ActionWrapper):
    def __init__(self, env):
        super().__init__(env)
        assert isinstance(env.action_space, gym.spaces.MultiDiscrete), \
            "Should only be used to wrap envs with MuliDiscrete actions."
        self.action_vec = self.action_space.nvec
        self.action_space = gym.spaces.Discrete(np.prod(self.action_vec))

    # def convert(act):
    #     discrete_act = 0
    #     for i, v in enumerate(act):
    #         discrete_act += (v * np.prod(self.action_vec[i+1:]))
    #     return discrete_act

    # def unconvert(discrete_act):
    #     act = np.zeros_like(self.action_vec)
    #     for i in range(len(self.action_vec)):
    #         act[i] = discrete_act // np.prod(self.action_vec[i+1:])
    #         discrete_act = discrete_act % np.prod(self.action_vec[i+1:])
    #     return act

    def action(self, discrete_act):
        act = np.zeros_like(self.action_vec)
        for i in range(len(self.action_vec)):
            act[i] = discrete_act // np.prod(self.action_vec[i + 1:])
            discrete_act = discrete_act % np.prod(self.action_vec[i + 1:])
        return act


class OnlineDictVectorizer():
    def __init__(self, n_features):
        self.n_features = n_features
        self.separator = '='
        self.dtype = np.float32
        self.reset()

    def reset(self):
        self.key = {}

    def fit(self, X):
        """
        Given a set of X, it updates the key with any new values.
        """

        for x in X:
            for f, v in x.items():
                if isinstance(v, str):
                    f = "%s%s%s" % (f, self.separator, v)
                if f not in self.key:
                    if len(self.key) < self.n_features:
                        self.key[f] = len(self.key)
                    else:
                        print("Exceeded available features")

        return self

    def transform(self, X):
        """
        Transforms the data using existing key mappings.
        """
        new_X = np.zeros((len(X), self.n_features), dtype=self.dtype)

        for i, x in enumerate(X):
            for f, v in x.items():
                if isinstance(v, str):
                    f = "%s%s%s" % (f, self.separator, v)
                    v = 1
                try:
                    new_X[i, self.key[f]] = self.dtype(v)
                except KeyError:
                    pass

        return new_X

    def fit_transform(self, X):
        """
        Similar to two calls of fit and transform, but does it all in
        one iteration rather than two through the data.
        """
        new_X = np.zeros((len(X), self.n_features), dtype=self.dtype)

        for i, x in enumerate(X):
            for f, v in x.items():
                if isinstance(v, str):
                    f = "%s%s%s" % (f, self.separator, v)
                    v = 1

                if f not in self.key:
                    if len(self.key) < self.n_features:
                        self.key[f] = len(self.key)
                    else:
                        print("Exceeded available features")

                try:
                    new_X[i, self.key[f]] = self.dtype(v)
                except KeyError:
                    pass

        return new_X


class BaseOppEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, tutor_class, max_depth=0):
        print('building env')
        self.tutor = tutor_class()

        self.max_depth = max_depth
        self.internal_memory = {}

        n_selections = len(self.tutor.get_possible_selections()) + 1
        n_operators = len(self.get_rl_operators())
        n_args = len(self.tutor.get_possible_args())

        branching = 0
        for opp, arg_count in self.get_rl_operators():
            branching += n_args**arg_count

        n_features = len(self.tutor.state) + branching**max_depth
        print('# features = %i' % n_features)

        self.dv = OnlineDictVectorizer(n_features=n_features)

        self.observation_space = spaces.Box(low=0.0,
                                            high=1.0,
                                            shape=(1, n_features),
                                            dtype=np.float32)
        self.action_space = spaces.MultiDiscrete(
            [n_selections, n_operators, n_args, n_args])

    def get_rl_operators(self):
        return [('copy', 1), ('add', 2), ('multiply', 2), ('mod10', 1),
                ('div10', 1)]

    def get_rl_state(self):
        # self.state = {
        #     'hundreds_carry': '',
        #     'tens_carry': '',
        #     'ones_carry': '',
        #     'upper_hundreds': upper_hundreds,
        #     'upper_tens': upper_tens,
        #     'upper_ones': upper_ones,
        #     'lower_hundreds': lower_hundreds,
        #     'lower_tens': lower_tens,
        #     'lower_ones': lower_ones,
        #     'operator': '+',
        #     'answer_thousands': '',
        #     'answer_hundreds': '',
        #     'answer_tens': '',
        #     'answer_ones': ''
        # }

        state = {}
        for attr in self.tutor.state:

            # TODO need generic way to handle this.
            if attr == "operator":
                continue

            # just whether or not there is a value
            state[attr] = self.tutor.state[attr] != ""

        # if its in internal memory, then return true, else false.
        for attr in self.internal_memory:
            state[attr] = True

        # relations (equality, >10)
        new_relations = {}

        for attr in state:
            attr_val = None
            if attr in self.tutor.state:
                attr_val = self.tutor.state[attr]
            elif attr in self.internal_memory:
                attr_val = self.internal_memory[attr]
            else:
                attr_val = ''

            # greater than 9
            try:
                new_relations['greater_than_9(%s)' %
                              str(attr)] = float(attr_val) > 9
            except Exception:
                new_relations['greater_than_9(%s)' % str(attr)] = False

        for attr in new_relations:
            state[attr] = new_relations[attr]

        from pprint import pprint
        pprint(state)

        return state
        # convert all attributes to strings
        # return {str(attr): state[attr] for attr in state}

    def step(self, action):
        try:
            s, a, i = self.decode(action)

            print(s, a, i)

            if isinstance(s, tuple):
                if s in self.internal_memory or i == '':
                    reward = -1
                else:
                    self.internal_memory[s] = i
                    reward = -0.01
            else:
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

        return obs, reward, done, info

    def apply_rl_op(self, op, arg1, arg2):
        a1 = None
        a2 = None

        if arg1 in self.tutor.state:
            a1 = self.tutor.state[arg1]
        elif arg1 in self.internal_memory:
            a1 = self.internal_memory[arg1]
        else:
            raise ValueError('Element not in memory')

        if arg2 in self.tutor.state:
            a2 = self.tutor.state[arg2]
        elif arg2 in self.internal_memory:
            a2 = self.internal_memory[arg2]
        else:
            raise ValueError('Element not in memory')

        if op == "copy":
            return a1
        elif op == "add":
            return str(int(a1) + int(a2))
        elif op == "multiply":
            return str(int(a1) * int(a2))
        elif op == "mod10":
            return str(int(a1) % 10)
        elif op == "div10":
            return str(int(a1) // 10)

    def decode(self, action):
        # print(action)

        op, arg_count = self.get_rl_operators()[action[1]]
        arg1 = self.tutor.get_possible_args()[action[2]]
        arg2 = self.tutor.get_possible_args()[action[3]]

        if action[0] == len(self.tutor.get_possible_selections()):
            if op == "copy":
                raise ValueError("cannot copy into internal memory")
            if arg_count == 1:
                s = (op, arg1)
            elif arg_count == 2:
                s = (op, arg1, arg2)
        else:
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
            v = self.apply_rl_op(op, arg1, arg2)

        i = {'value': str(v)}

        return s, a, i

    def reset(self):
        self.tutor.set_random_problem()
        state = self.get_rl_state()
        self.internal_memory = {}
        obs = self.dv.transform([state])[0]
        return obs

    def render(self, mode='human', close=False):
        self.tutor.render()
