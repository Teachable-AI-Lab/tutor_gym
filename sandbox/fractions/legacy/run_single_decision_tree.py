import gym
from tutorenvs.fractions import FractionArithSymbolic

from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction import DictVectorizer
from tutorenvs.utils import OnlineDictVectorizer

from tutorenvs.utils import DataShopLogger
import numpy as np


def train_tree(n=10, logger=None):
    X = []
    y = []
    # dv = OnlineDictVectorizer(200)
    dv = DictVectorizer()
    actions = []
    action_mapping = {}
    rev_action_mapping = {}
    tree = DecisionTreeClassifier()
    env = FractionArithSymbolic(logger)

    p = 0
    hints = 0

    Xv = None

    while p < n:

        # make a copy of the state
        state = {a: env.state[a] for a in env.state}
        # print(state)
        # env.render()

        if rev_action_mapping == {}:
            sai = None
        else:
            vstate = dv.transform([state])
            # print(vstate)
            # print('vstate', vstate)
            # print(tree.predict(vstate))
            # print(rev_action_mapping)
            sai = rev_action_mapping[tree.predict(vstate)[0]]
            # print(sai)

        if sai is None:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])

        reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})
        # print('reward', reward, sai)

        if reward < 0:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            # print("demo", sai)
            sai = (sai[0], sai[1], sai[2]['value'])
            reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})

        X.append(state)
        y.append(sai)

        Xv = dv.fit_transform(X)

        # if Xv is None:
        #     Xv = dv.fit_transform([state])
        #     # print(Xv, state)
        # else:
        #     Xv = np.concatenate((Xv, dv.fit_transform([state])))

        # print('shape', Xv.shape)
        actions = set(y)
        action_mapping = {l: i for i, l in enumerate(actions)}
        rev_action_mapping = {i: l for i, l in enumerate(actions)}
        yv = np.array([action_mapping[l] for l in y])
        # print(yv)
# 
        # print(Xv.shape, yv.shape, yv[-5:])

        tree.fit(Xv, yv)

        if sai[0] == "done" and reward == 1.0:
            if(p % 50 == 0):
                print("Problem %s of %s" % (p, n))
                print("# of hints = {}".format(hints))
            hints = 0

            p += 1

    return tree


if __name__ == "__main__":

    logger = DataShopLogger('FractionsTutor', extra_kcs=['field'])
    for _ in range(1):
        tree = train_tree(30000, logger)
