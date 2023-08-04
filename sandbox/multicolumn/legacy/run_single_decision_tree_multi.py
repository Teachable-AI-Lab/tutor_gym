import gym
# from stable_baselines.common import make_vec_env
# from stable_baselines.common.policies import MlpPolicy
# from stable_baselines import PPO2
import tutorenvs
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.multicolumn import MultiColumnAdditionSymbolic
import numpy as np

from sklearn.tree import DecisionTreeClassifier
# from sklearn.feature_extraction import DictVectorizer

from tutorenvs.utils import OnlineDictVectorizer
from tutorenvs.utils import DataShopLogger

def train_tree(n=10, logger=None):
    X = []
    y = []
    dv = OnlineDictVectorizer(110)
    actions = []
    action_mapping = {}
    rev_action_mapping = {}
    tree = DecisionTreeClassifier()
    env = MultiColumnAdditionSymbolic(logger=logger)

    hints= 0
    p = 0

    Xv = None

    while p < n:
        # make a copy of the state
        state = {a: env.state[a] for a in env.state}
        # env.render()

        if rev_action_mapping == {}:
            sai = None
        else:
            vstate = dv.transform([state])
            sai = rev_action_mapping[tree.predict(vstate)[0]]

        if sai is None:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])

        reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})
        # print('reward', reward)

        if reward < 0:
            hints += 1
            # print('hint')
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])
            reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})

        # X.append(state)
        y.append(sai)

        if Xv is None:
            Xv = dv.fit_transform([state])
        else:
            Xv = np.concatenate((Xv, dv.fit_transform([state])))

        # print('shape', Xv.shape)
        actions = set(y)
        action_mapping = {l: i for i, l in enumerate(actions)}
        rev_action_mapping = {i: l for i, l in enumerate(actions)}
        yv = [action_mapping[l] for l in y]

        tree.fit(Xv, yv)

        if sai[0] == "done" and reward == 1.0:
            if(p % 50 == 0):
                print("Problem %s of %s" % (p, n))
                print("# of hints = {}".format(hints))
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
