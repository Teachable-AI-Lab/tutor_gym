import gym
# from stable_baselines.common import make_vec_env
# from stable_baselines.common.policies import MlpPolicy
# from stable_baselines import PPO2
import tutorenvs
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.multicolumn import MultiColumnAdditionSymbolic
import numpy as np

from sklearn.tree import DecisionTreeClassifier
from numbaILP.splitter import TreeClassifier, DecisionTree2
# from apprentice.learners.WhenLearner import DecisionTree2
# from sklearn.feature_extraction import DictVectorizer

from tutorenvs.utils import OnlineDictVectorizer
from tutorenvs.utils import DataShopLogger
import time

def train_tree(n=10, logger=None):
    X = []
    # y = []
    yv = []
    # action_mapping = {}
    # dv = OnlineDictVectorizer(110)
    # actions = set()
    action_mapping = {}
    rev_action_mapping = {}
    # tree = DecisionTreeClassifier()
    tree = DecisionTree2(impl="decision_tree")
    # tree = DecisionTree2(impl="sklearn")
    # self.dt = TreeClassifier(impl)
    env = MultiColumnAdditionSymbolic(logger=logger)

    hints= 0
    p = 0

    Xv = None

    while p < n:
        # make a copy of the state
        state = {a: env.state[a] for a in env.state}
        # env.render()

        if len(rev_action_mapping) == 0:
            sai = None
        else:
            # vstate = dv.transform([state])
            p_t0 = time.time_ns()
            sai = rev_action_mapping[tree.predict([state])[0]]
            p_t1 = time.time_ns()
            

        if sai is None:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])

        reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})
        # print('reward', sai, reward)

        if reward < 0:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])
            reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})

        # X.append(state)
        # y.append(sai)
        # actions.add(sai)
        if(sai not in action_mapping):
            ind = len(action_mapping)
            rev_action_mapping[ind] = sai
            action_mapping[sai] = ind

        # yv.append(action_mapping[sai])

        f_t0 = time.time_ns()
        tree.ifit(state,action_mapping[sai])
        # print(sai, action_mapping[sai])
        f_t1 = time.time_ns()



        # if Xv is None:
        #     Xv = dv.fit_transform([state])
        # else:
        #     Xv = np.concatenate((Xv, dv.fit_transform([state])))

        # print('shape', Xv.shape)
        # actions = set(y)
        # action_mapping = {l: i for i, l in enumerate(actions)}
        # rev_action_mapping = {i: l for i, l in enumerate(actions)}
        # yv = [action_mapping[l] for l in y]


        # tree.fit(Xv, yv)

        if sai[0] == "done" and reward == 1.0:
            if(p % 50 == 0):
                print("Problem %s of %s" % (p, n))
                # print("# of hints = {}".format(hints))
                print(f"predict: {(p_t1-p_t0)/1000.0} ms")
                print(f"fit: {(f_t1-f_t0)/1000.0} ms")
            hints = 0

            p += 1

    return tree

if __name__ == "__main__":

    logger = DataShopLogger('MulticolumnAdditionTutor', extra_kcs=['field'])
    for _ in range(1):
        tree = train_tree(30000, logger)
    # env = MultiColumnAdditionSymbolic()

    # while True:
    #     sai = env.request_demo()
    #     env.apply_sai(sai[0], sai[1], sai[2])
    #     env.render()
