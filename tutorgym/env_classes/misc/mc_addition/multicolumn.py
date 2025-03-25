from random import randint
from random import choice
from pprint import pprint
import logging

import gym
from gym import error, spaces, utils
from gym.utils import seeding
from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction import DictVectorizer
import numpy as np
# from PIL import Image, ImageDraw
# from colorama import Back, Fore
import hashlib
from base64 import b64encode

from tutorgym.utils import OnlineDictVectorizer
from tutorgym.utils import DataShopLogger
from tutorgym.utils import StubLogger

# Note: Transforming the problem state into a MemSet lets us
#  build a long cryptographic hash from it to simplify state-machine. 
# from cre.transform import MemSetBuilder
from itertools import permutations

from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor



# ----------------------------------
# : MultiColumnAddition

def to_int_safe(a):
    if(a == ""):
        return 0
    try:
        v = int(a)
    except:
        v = 0
    return v


class MultiColumnAddition(StateMachineTutor):

    def __init__(self, n_digits=3, pad_zeros=False, carry_zero=False, random_n_digits=False, **kwargs):
        super().__init__(**kwargs)                
        self.problem = None
        self.n_digits = n_digits
        self.pad_zeros = pad_zeros
        self.carry_zero = carry_zero
        self.random_n_digits = random_n_digits
        # self.logger.set_student()
        self.set_random_problem()

    # ------------------
    # : Problem Start State Initialization 

    def _standardize_problem(self, upper, lower, **kwargs):
        n_digits = kwargs.get('n_digits', self.n_digits)
        pad_zeros = kwargs.get('pad_zeros', self.pad_zeros)

        upper = str(upper)
        lower = str(lower)

        N = max(len(upper), len(lower))
        if(n_digits is not None):
            assert N <= n_digits, f"Fixed n_digits={n_digits} too small for {upper}+{lower}."
            N = n_digits

        if(pad_zeros):
            upper = upper.zfill(N)
            lower = lower.zfill(N)

        return upper, lower, N

    def _blank_state(self, N):
        # Make blank: state (i.e. static interface before setting start state)
        start_params = {'type': 'TextField', "locked" : True, "value" : ""}
        field_params = {'type': 'TextField', "locked" : False, "value" : ""}
        button_params = {'type': 'Button'}

        state = {
            # "operator" : {"x" :-110,"y" : 220 , "width" : 100, "height" : 100, **start_params},
            # "line" :     {"x" :0,   "y" : 325 , "width" : 5, "height" : 5},
            "hint" :     {"x" :N * 110, "y" : 440 , "width" : 100, "height" : 100, **button_params},
            "done" :     {"x" :N * 110, "y" : 550 , "width" : 100, "height" : 100, **button_params},
            "hidey1" :   {"x" :N * 110, "y" : 0 , "width" : 100, "height" : 100, **start_params},
            "hidey2" :   {"x" :0,   "y" : 110 , "width" : 100, "height" : 100, **start_params},
            "hidey3" :   {"x" :0,   "y" : 220 , "width" : 100, "height" : 100, **start_params},
        }

        # Do inpA/inpB and carry/ans seperately so inputs show up first in state
        #  makes it easier to see state edit progression.
        for i in range(N):
            offset = (N-i) * 110
            state.update({
                f"inpA{i+1}" : {"x" :offset,   "y" : 110 , "width" : 100, "height" : 100, **start_params},
                f"inpB{i+1}" : {"x" :offset,   "y" : 220 , "width" : 100, "height" : 100, **start_params},
            })

        for i in range(N):
            offset = (N-i) * 110
            if(i != 0):
                state.update({
                    f"carry{i}" : {"x" :offset,   "y" : 0 , "width" : 100, "height" : 100, **field_params},
                })
            state.update({
                f"out{i+1}" : {"x" :offset,   "y" : 330 , "width" : 100, "height" : 100, **field_params},
            })

        state.update({
            f"carry{N}" : {"x" :0,   "y" : 0 , "width" : 100, "height" : 100, **field_params},
            f"out{N+1}" : {"x" :0,   "y" : 330 , "width" : 100, "height" : 100, **field_params},
        })

        inpAs = [f'inpA{i}' for i in range(1,N+1)]
        inpBs = [f'inpB{i}'  for i in range(1,N+1)]
        outs = [f'out{i}' for i in range(1,N+2)]
        carries = [f'carry{i}' for i in range(1,N+1)]
        self.possible_selections = outs + carries + ['done']
        self.possible_args = inpAs + inpBs + carries

        # Ensure all have an id attribute
        for key, obj in state.items():
            state[key]['id'] = key

        ordered_state = {}
        order = [*reversed(inpAs), *reversed(inpBs), *reversed(outs), *reversed(carries),
                    'hidey1', 'hidey2', 'hidey3', 'hint', 'done']
        for key in order:
            ordered_state[key] = state[key]
        state = ordered_state

        return ProblemState(state)


    def set_start_state(self, upper, lower, **kwargs):
        # pad_zeros = kwargs.get('pad_zeros', self.pad_zeros)
        # n_digits = kwargs.get('n_digits', self.n_digits)
        ''' Domain implementation: Used by StateMachineTutor.set_problem() 
            to initialize a start state.'''
        upper, lower, N =  self._standardize_problem(
                            upper, lower, **kwargs)
        self.problem = (upper, lower) 

        state = self._blank_state(N)
        for i in range(N):
            if(i < len(upper)):
                state[f'inpA{i+1}']['value'] = upper[-i-1]
            if(i < len(lower)):
                state[f'inpB{i+1}']['value'] = lower[-i-1]
        self.start_state = ProblemState(state)
        self.problem_name = f"{upper}+{lower}"
        

    def set_random_problem(self, **kwargs):
        random_n_digits = kwargs.get('random_n_digits', self.random_n_digits)
        if(random_n_digits):
            n_top = randint(1, self.n_digits)
            n_bot = randint(1, self.n_digits)
            if(n_bot > n_top): 
                n_top, n_bot = n_bot, n_top
        else:
            n_top = n_bot = kwargs.get('n_digits', self.n_digits)

        upper = str(randint(10 ** (n_top-1), (10 ** n_top) - 1))
        lower = str(randint(10 ** (n_bot-1), (10 ** n_bot) - 1))

        self.set_problem(upper, lower, **kwargs)

        return (upper, lower)

    # --------------------------
    # : Problem State Machine Initialization

    def create_fsm(self, state):
        ''' Domain implementation: Used by StateMachineTutor.set_problem() 
            to initialize an FSM for this domain.'''
        prev_carry = False

        curr_state = state.copy()
        fsm = FiniteStateMachine(curr_state)        

        # Make FSM one column at a time
        i = 0
        while(True):
            argA, argB = f'inpA{i+1}', f'inpB{i+1}'
            if(argA not in state.objs or argB not in state.objs):
                break

            upper = state[argA]['value']
            lower = state[argB]['value']
            p_carry = ""
            if(f"carry{i}" in curr_state.objs):
                p_carry = curr_state[f"carry{i}"]['value']
                # print("P CARRY", p_carry)
            
            # print(i, "$", upper, lower, p_carry)
            partial_sum = to_int_safe(upper) + to_int_safe(lower) + to_int_safe(prev_carry)
            if(partial_sum == 0 and lower == "" and upper == ""):
                prev_carry = 0
                i += 1
                break
            # print(partial_sum)
            # print(':', f'{argA}={upper}', f'{argB}={lower}')
            if(lower == ""):
                # If both lower and upper are empty
                #  then don't fill the next column
                if(upper == "" and prev_carry):
                    # Copy down a lone carry item
                    foci = [f'carry{i}']
                    sai = (f'out{i+1}', 'UpdateTextField',
                            "1" if prev_carry else "0")
                    act = Action(sai, args=foci, how_help="Copy(a)")
                    curr_state = fsm.add_edge(curr_state, act)

                    # a_sai = (f'out{i+1}', 'UpdateTextField',
                    #             {'value': str(partial_sum % 10)})
                    # a_act = Action(a_sai, args=foci, how_help="OnesDigit(Add(a,b))")

                # partial_sum = to_int_safe(upper)

                elif(p_carry):                    
                    foci = [f'carry{i}', f'inpA{i+1}']
                    # partial_sum += 1

                    a_sai = (f'out{i+1}', 'UpdateTextField',
                                str(partial_sum % 10))
                    a_act = Action(a_sai, args=foci, how_help="OnesDigit(Add(a,b))")
                    
                    if(self.carry_zero or partial_sum >= 10):
                        
                        c_sai = (f'carry{i+1}', 'UpdateTextField',
                                str(partial_sum // 10))
                        c_act = Action(c_sai, args=foci, how_help="TensDigit(Add(a,b))")

                        # print("Case A:", a_act, c_act, i)
                        curr_state = fsm.add_unordered(curr_state, [a_act, c_act])
                        
                    else:
                        # print("Case B:", a_act, i)
                        curr_state = fsm.add_edge(curr_state, a_act)
                else:
                    # Copy down a lone upper item
                    if(upper != ""):
                        foci = [f'inpA{i+1}']
                        sai = (f'out{i+1}', 'UpdateTextField',
                                str(partial_sum))
                        act = Action(sai, args=foci, how_help="Copy(a)")
                        curr_state = fsm.add_edge(curr_state, act)
                        # print("Case C", act, i)
                        
            elif(upper != ""):
                # partial_sum = to_int_safe(upper) + to_int_safe(lower)

                foci = [f'inpA{i+1}', f'inpB{i+1}']
                if p_carry != "":
                    # partial_sum += 1
                    foci = [f'carry{i}',*foci]

                if self.carry_zero or partial_sum >= 10:
                    a_sai = (f'out{i+1}', 'UpdateTextField', 
                                str(partial_sum % 10))
                    a_act = Action(a_sai, args=foci, how_help=f"OnesDigit(Add({','.join(['a','b','c'][:len(foci)])}))")

                    c_sai = (f'carry{i+1}', 'UpdateTextField',
                                str(partial_sum // 10))
                    c_act = Action(c_sai, args=foci, how_help=f"TensDigit(Add({','.join(['a','b','c'][:len(foci)])}))")
                    # print("Case D:", a_act, c_act, i)
                    curr_state = fsm.add_unordered(curr_state, [a_act, c_act])

                else:
                    sai = (f'out{i+1}', 'UpdateTextField',
                            str(partial_sum))
                    act = Action(sai, args=foci, how_help=f"OnesDigit(Add({','.join(['a','b','c'][:len(foci)])}))")
                    # print("Case E:", act, i)
                    curr_state = fsm.add_edge(curr_state, act)
            else:
                raise ValueError("Shouldn't happen")

            prev_carry = partial_sum >= 10
            i += 1
        N = i

        # Copy down hanging carry
        if prev_carry:
            foci = [f'carry{i}']
            sai = (f'out{i+1}', 'UpdateTextField',
                    "1" if prev_carry else "0")
            act = Action(sai, args=foci, how_help="Copy(a)")
            curr_state = fsm.add_edge(curr_state, act)
            # print("Case F:", act, i)

        act = Action(('done', "PressButton", -1))
        curr_state = fsm.add_edge(curr_state, act, is_done=True)
        # print("curr_state:", curr_state)

        return fsm

    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args

# class MultiColumnAdditionDigitsGymEnv(gym.Env):
#     metadata = {'render.modes': ['human']}

#     def __init__(self, logger=None, **kwargs):
#         self.tutor = MultiColumnAddition(**kwargs)
#         n_selections = len(self.tutor.get_possible_selections())
#         n_features = (11+2)*len(self.tutor.get_state())
#         #print("N FEATERS", n_features)
#         self.dv = OnlineDictVectorizer(n_features)
#         self.observation_space = spaces.Box(low=0.0,
#                 high=1.0, shape=(1, n_features), dtype=np.float32)
#         self.action_space = spaces.MultiDiscrete([n_selections, 10])
#         self.n_steps = 0
#         self.max_steps = 5000


#         if logger is None:
#             self.logger = DataShopLogger("MultiColumnAdditionDigitsGymEnv", extra_kcs=['field'])
#         else:
#             self.logger = logger
#         self.logger.set_student()



#     def get_rl_state(self):
#         d = {}
#         for _id, obj in self.tutor.get_state().items():
#             d[(_id, 'value')] = obj.get('value', '')
#             d[(_id, 'locked')] = obj.get('locked', True)
#         return d

#     def step(self, action, apply_incorrects=False):
#         self.n_steps += 1

#         sai = self.decode(action)
#         # print("DECODE", sai)
#         # print()
#         reward = self.tutor.check(sai)
#         if(reward >= 0 or apply_incorrects):
#             self.tutor.apply(sai)

#         outcome = "CORRECT" if reward > 0 else "INCORRECT"
#         s, a, inp = sai
#         # print("LOG", s, a, i['value'], outcome)
#         self.logger.log_step(s, a, inp, outcome, step_name=s, kcs=[s])
        
#         rl_state = self.get_rl_state()

#         obs = self.dv.fit_transform([rl_state])[0]

#         done = (sai[0] == 'done' and reward == 1.0)

#         # have a max steps for a given problem.
#         # When we hit that we're done regardless.
#         if self.n_steps > self.max_steps:
#             done = True

#         info = {}

#         return obs, reward, done, info

#     def encode(self, sai):
#         s,a,i = sai
#         v = i['value']
#         out = np.zeros(1,dtype=np.int64)
#         enc_s = self.tutor.get_possible_selections().index(s)
#         if(s == 'done' or s == "check_convert"):
#             v = 0
#         # n = len(self.tutor.get_possible_selections()) 
#         out[0] = 10 * enc_s + int(v) 
#         return out

#     def request_demo_encoded(self):
#         action = self.tutor.get_demo() 

#         # Log demo
#         sai = action.sai
#         feedback_text = f"selection: {sai[0]}, action: {sai[1]}, input: {sai[2]['value']}"
#         self.logger.log_hint(feedback_text, step_name=sai[0], kcs=[sai[0]])
        
#         return self.encode(action.sai)


#     def decode(self, action):
#         # print(action)
#         s = self.tutor.get_possible_selections()[action[0]]

#         if s == "done":
#             a = "PressButton"
#         else:
#             a = "UpdateTextField"
        
#         if s == 'done' or s == "check_convert":
#             v = -1
#         else:
#             v = str(action[1])
        
#         i = {'value': v}

#         return s, a, i

#     def reset(self):
#         self.n_steps = 0
#         self.tutor.set_random_problem()

#         (upper, lower), _ = self.tutor.problem_config
#         self.logger.set_problem("%s_%s" % (upper, lower))
        
#         rl_state = self.get_rl_state()
#         # print("rl_state", rl_state)
#         obs = self.dv.fit_transform([rl_state])[0]
#         return obs

#     def render(self, mode='human', close=False):
#         self.tutor.render()


# -------------------------
# : Sanity Tests
    
def test_basic():
    mc = MultiColumnAddition()
    mc.set_problem("567", "689")
    for i in range(8):
        action = mc.get_demo()
        reward = mc.check(action)
        nxt = mc.get_all_demos()
        assert len(nxt) <= 2

        if(i != 7):
            assert mc.check(('done','PressButton', {"value": -1})) == -1
            assert not mc.is_done
        mc.apply(action)
        print(action, mc.state)
    assert mc.is_done
    assert mc.state["out1"]['value'] == "6"
    assert mc.state["out2"]['value'] == "5"
    assert mc.state["out3"]['value'] == "2"
    assert mc.state["out4"]['value'] == "1"

    mc.set_problem("333", "333")
    for i in range(4):
        action = mc.get_demo()
        reward = mc.check(action)
        nxt = mc.get_all_demos()
        assert len(nxt) == 1
        if(i != 3):
            assert mc.check(('done','PressButton', {"value": -1})) == -1
            assert not mc.is_done
        # print("CHECK", reward, ))
        mc.apply(action)
        print(action, mc.state)        
    assert mc.is_done
    assert mc.state["out1"]['value'] == "6"
    assert mc.state["out2"]['value'] == "6"
    assert mc.state["out3"]['value'] == "6"
    assert mc.state["out4"]['value'] == ""

    mc.set_problem("333", "3")
    for i in range(4):
        action = mc.get_demo()
        reward = mc.check(action)
        nxt = mc.get_all_demos()
        assert len(nxt) == 1
        if(i != 3):
            assert mc.check(('done','PressButton', {"value": -1})) == -1
            assert not mc.is_done

        mc.apply(action)
        print(action, mc.state)
    assert mc.is_done
    assert mc.state["out1"]['value'] == "6"
    assert mc.state["out2"]['value'] == "3"
    assert mc.state["out3"]['value'] == "3"
    assert mc.state["out4"]['value'] == ""


    mc.set_problem("391", "9")
    for i in range(6):
        action = mc.get_demo()
        reward = mc.check(action)
        nxt = mc.get_all_demos()
        if(i != 5):
            assert mc.check(('done','PressButton', {"value": -1})) == -1
            assert not mc.is_done

        mc.apply(action)
        print(action, mc.state)
    assert mc.is_done
    assert mc.state["out1"]['value'] == "0"
    assert mc.state["out2"]['value'] == "0"
    assert mc.state["out3"]['value'] == "4"
    assert mc.state["out4"]['value'] == ""


def test_demo_check():
    mc = MultiColumnAddition(check_args=True, check_how=False, demo_args=True, demo_how=True)
    mc.set_problem("567", "689")
    nxt = mc.get_all_demos()

    assert nxt[0].args is not None and nxt[0].how_help is not None

    # Should Fail Without args
    actA = Action(("out1", "UpdateTextField", {"value": '6'}))
    actC = Action(("carry1", "UpdateTextField", {"value": '1'}))
    assert mc.check(actA)==-1
    assert mc.check(actC)==-1

    # Succeed with args
    foci = ["inpA1", "inpB1"]
    actA = Action(("out1", "UpdateTextField", {"value": '6'}), args=foci)
    actC = Action(("carry1", "UpdateTextField", {"value": '1'}), args=foci)
    assert mc.check(actA)==1
    assert mc.check(actC)==1



if __name__ == "__main__":
    # mc = MultiColumnAddition()
    # mc.set_problem("567", "689")
    # for key, obj in mc.state.objs.items():
    #     print(key, obj)

    # for key, obj in mc.fsm.nodes.items():
    #     print(key, [f"{x.sai.selection}->{x.sai.inputs['value']} : {ns}" for x, ns in obj['edges'].items()])

    # test_basic()
    # test_demo_check()

    
    mc = MultiColumnAddition(carry_zero=True)
    
    mc.set_problem("67", "2")
    for key, obj in mc.fsm.nodes.items():
        print(key, [f"{x.sai.selection}->{x.sai.inputs['value']} : {ns}" for x, ns in obj['edges'].items()])


    mc = MultiColumnAddition(carry_zero=True, random_n_digits=True)
    print("------")
    for i in range(100):
        # mc.set_problem("100", "2")
        mc.set_random_problem()
        end_node = [x for x in mc.fsm.nodes.values() if len(x['edges']) and list(x['edges'])[0].sai.selection == "done"][0]
        objs = end_node['state'].objs
        gv = lambda x: objs[x]['value']
        s = "".join([gv('out4'), gv('out3'), gv('out2'), gv('out1')])
        upper, lower = mc.problem
        _sum = to_int_safe(upper) + to_int_safe(lower)
        # gc = lambda x: objs[x]['value']
        print("".join([gv('carry3'), gv('carry2'), gv('carry1')]))
        print(f"{upper}+{lower}={_sum}={s}")
        assert str(_sum) == s
        


    
    # print("::", nxt)
    # print("::", [actA, actC])
    # print(mc.check(actA), mc.check(actC))


