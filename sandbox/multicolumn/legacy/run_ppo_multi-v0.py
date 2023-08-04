import gym
from stable_baselines.common import make_vec_env
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.policies import CnnPolicy
from stable_baselines import PPO2
import tutorenvs
import numpy as np


if __name__ == "__main__":

    # multiprocess environment
    env = make_vec_env('MultiColumnArith-v0', n_envs=1)
    model = PPO2(MlpPolicy, env, verbose=1,
            gamma=0.5,
            policy_kwargs={'net_arch': [65, 65, {'vf': [65], 'pi': [65]}]},
            tensorboard_log="./tensorboard/v0/")

    while True:
        # Train
        model.learn(total_timesteps=100)

        # Test
        # obs = env.reset()
        # rwd = 0
        # for _ in range(10000):
        #     action, _states = model.predict(obs)
        #     obs, rewards, dones, info = env.step(action)
        #     rwd += np.sum(rewards)
        #     env.render()
        # print(rwd)
