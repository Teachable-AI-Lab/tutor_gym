import numpy as np
import gym
from stable_baselines3.ppo import PPO
from stable_baselines3.ppo import MlpPolicy

from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
from tutorenvs.forcedemo import ForceDemoMixin
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
        env = gym.make('MulticolumnArithSymbolic-v0')
        env = MultiDiscreteToDiscreteWrapper(env)

        # make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = MultiDiscreteToDiscreteWrapper(MultiColumnAdditionDigitsEnv())
        model = PPO(MlpPolicy, env, 
                    # max_incorrect=1,
                    verbose=1,
                    learning_rate=0.0005,
                    batch_size=256,
                    # train_freq=-1,
                    # n_episodes_rollout=1,
                    # exploration_fraction=0.1,
                    # exploration_initial_eps=0.45,
                    # exploration_final_eps=0.0,
                    gamma=0.4,
                    # learning_starts=1,
                    policy_kwargs={'net_arch': [200, 200, 200]}, # {'qf': [65], 'pi': [65]}]},
                    tensorboard_log="./tensorboard_dqn_multi/"
                    )
                # gamma=0.1,
                # tensorboard_log="./tensorboard/v0/")


        # while True:
        model.learn(total_timesteps=300000)
        # model.save('multi-v3')

        # To demonstrate saving and loading
        # model.save("ppo2_multicolumn-v0")
        # del model
        # model = PPO2.load("ppo2_multicolumn-v0")

        # Enjoy trained agent
        # obs = env.reset()
        # rwd = 0
        # for _ in range(3000000):
        #     action, _states = model.predict(np.expand_dims(obs,0))
        #     obs, rewards, dones, info = env.step(action)
        #     print(dones)
        #     rwd += np.sum(rewards)
        #     env.render()
        # print(rwd)

    # while True:
    #     # Train
    #     model.learn(total_timesteps=1000000)

    #     # Test
    #     # obs = env.reset()
    #     # rwd = 0
    #     # for _ in range(10000):
    #     #     action, _states = model.predict(obs)
    #     #     obs, rewards, dones, info = env.step(action)
    #     #     rwd += np.sum(rewards)
    #     #     env.render()
    #     # print(rwd)
