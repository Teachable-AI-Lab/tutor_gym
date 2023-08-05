import numpy as np
import gym
from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy

from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.forcedemo import ForceDemoMixin
import os
# from stable_baselines.common.cmd_util import make_vec_env


# # 
class DQN_w_Demos(ForceDemoMixin, DQN):
    def __init__(self, policy, env, incorr_bef_demo=5, **kwargs):
        self.incorr_bef_demo = incorr_bef_demo
        DQN.__init__(self, policy, env,**kwargs)

# class PPO_w_Demos(ForceDemoMixin, PPO):
#     def __init__(self, policy, env, max_incorrect=5, **kwargs):
#         self.max_incorrect = max_incorrect
#         DQN.__init__(self, policy, env,**kwargs)



if __name__ == "__main__":
    for i in range(10):
        os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
        # multiprocess environment

        env = gym.make('MulticolumnAdditionSTD_SZ-v0')
        env.logger = DataShopLogger("mc_std_sz_dqn_demo", output_dir="log_dqn_demo")
        env = MultiDiscreteToDiscreteWrapper(env)
        # env = make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = MultiDiscreteToDiscreteWrapper(MultiColumnAdditionDigitsEnv())
        model = DQN_w_Demos(MlpPolicy, env, 
                    incorr_bef_demo=1,
                    verbose=1,
                    learning_rate=0.0003,
                    batch_size=256,
                    exploration_fraction=0.1,
                    exploration_initial_eps=0.45,
                    exploration_final_eps=0.0,
                    gamma=0.0,
                    learning_starts=1,
                    policy_kwargs={'net_arch': [200, 200]}, # {'qf': [65], 'pi': [65]}]},
                    tensorboard_log="./tensorboard_dqn_demo_multi/"
                    )
        model.learn(total_timesteps=300000)
        
