import numpy as np
import gym
from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy

from tutorenvs.utils import DataShopLogger
from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.forcedemo import ForceDemoMixin
import os

if __name__ == "__main__":
    for i in range(10):
        os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
        logger = DataShopLogger("fr_dqn", output_dir="log_dqn")
        env = gym.make('FractionArith-v0', extra_kcs=['field'], logger=logger)
        env = MultiDiscreteToDiscreteWrapper(env)
        model = DQN(MlpPolicy, env, 
                    verbose=1,
                    learning_rate=0.0003,
                    batch_size=256,
                    exploration_fraction=0.1,
                    exploration_initial_eps=0.45,
                    exploration_final_eps=0.0,
                    gamma=0.0,
                    learning_starts=1,
                    policy_kwargs={'net_arch': [200, 200]}, # {'qf': [65], 'pi': [65]}]},
                    tensorboard_log="./tensorboard_dqn_frac/"
                    )

        model.learn(total_timesteps=300000)
        
