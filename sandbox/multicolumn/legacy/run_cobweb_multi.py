import gym
from stable_baselines.common import make_vec_env
from stable_baselines.common.policies import MlpPolicy
from stable_baselines import PPO2
import tutorenvs
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.multicolumn import MultiColumnAdditionSymbolic
import numpy as np
from pprint import pprint

from concept_formation.cobweb3 import Cobweb3Tree
from concept_formation.visualize import visualize

from tutorenvs.utils import DataShopLogger

def train_tree(n=10, logger=None):
    tree = Cobweb3Tree()
    env = MultiColumnAdditionSymbolic(logger=logger)

    p = 0
    nhints = 0
    while p < n:
        # make a copy of the state
        state = {a: env.state[a] for a in env.state}
        env.render()

        concept = tree.categorize(state)
        sel = concept.predict('selection')
        inp = concept.predict('input')

        if sel == "done":
            act = 'ButtonPressed'
        else:
            act = "UpdateField"

        sai = (sel, act, inp)

        if sel is None or inp is None:
            nhints += 1
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])

        reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})
        # print('reward', reward)

        if reward < 0:
            nhints += 1
            sai = env.request_demo()
            sai = (sai[0], sai[1], sai[2]['value'])
            reward = env.apply_sai(sai[0], sai[1], {'value': sai[2]})

        state['selection'] = sai[0]
        state['input'] = str(sai[2])
        tree.ifit(state)
        
        if sai[0] == "done" and reward == 1.0:
            print('# hints =', nhints)
            nhints = 0
            print("Problem %s of %s" % (p, n))
            p += 1

    return tree

if __name__ == "__main__":

    logger = DataShopLogger('MulticolumnAdditionTutor', extra_kcs=['field'])
    for _ in range(1):
        tree = train_tree(200, logger)
    visualize(tree)

    # env = MultiColumnAdditionSymbolic()

    # while True:
    #     sai = env.request_demo()
    #     env.apply_sai(sai[0], sai[1], sai[2])
    #     env.render()
