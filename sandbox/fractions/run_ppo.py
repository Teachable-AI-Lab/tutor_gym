import numpy as np
import gym
from stable_baselines3.ppo import PPO
from stable_baselines3.ppo import MlpPolicy

from tutorenvs.utils import DataShopLogger
from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.forcedemo import ForceDemoMixin
from tutorenvs.utils import linear_schedule
import os

if __name__ == "__main__":
    for i in range(10):
        os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
        env = gym.make('FractionArith-v0')
        env.logger = DataShopLogger("fr_ppo", output_dir="log_ppo")
        env = MultiDiscreteToDiscreteWrapper(env)        
        model = PPO(MlpPolicy, env, 
                    verbose=1,
                    learning_rate=linear_schedule(0.0003),
                    batch_size=256,                    
                    gamma=0.0,
                    policy_kwargs={'net_arch': [200, 200]},
                    tensorboard_log="./tensorboard_ppo_frac/"
                    )

        model.learn(total_timesteps=300000)
        
