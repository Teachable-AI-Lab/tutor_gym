import numpy as np
import gym
from stable_baselines3.ppo import PPO
from stable_baselines3.ppo import MlpPolicy

from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.forcedemo import ForceDemoMixin
from tutorenvs.utils import linear_schedule
import os
# from stable_baselines.common.cmd_util import make_vec_env


# # 
# class PPO_w_Demos(ForceDemoMixin, PPO):
#     def __init__(self, policy, env, max_incorrect=5, **kwargs):
#         self.max_incorrect = max_incorrect
#         PPO.__init__(self, policy, env,**kwargs)
        # self.collect_rollouts = ForceDemoMixin.collect_rollouts

# class PPO_w_Demos(ForceDemoMixin, PPO):
#     def __init__(self, policy, env, max_incorrect=5, **kwargs):
#         self.max_incorrect = max_incorrect
#         DQN.__init__(self, policy, env,**kwargs)



if __name__ == "__main__":
    for i in range(10):
        os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
        # multiprocess environment
        env = gym.make('MulticolumnAdditionSTD_SZ-v0')
        env.logger = DataShopLogger("mc_std_sz_ppo", output_dir="log_ppo")
        env = MultiDiscreteToDiscreteWrapper(env)

        # make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = MultiDiscreteToDiscreteWrapper(MultiColumnAdditionDigitsEnv())
        model = PPO(MlpPolicy, env, 
                    verbose=1,
                    learning_rate=linear_schedule(0.0003),
                    batch_size=256,
                    gamma=0.0, # No need for discount factor since immediate feedback
                    policy_kwargs={'net_arch': [200, 200]}, 
                    tensorboard_log="./tensorboard_ppo_multi/"
                    )


        model.learn(total_timesteps=500000)
        
