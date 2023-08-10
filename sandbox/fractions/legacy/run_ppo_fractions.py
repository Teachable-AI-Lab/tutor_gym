import gym
from stable_baselines.common import make_vec_env
from stable_baselines.common.policies import MlpPolicy
from stable_baselines import PPO2
from stable_baselines import SAC
import tutorenvs
import numpy as np


if __name__ == "__main__":

    # multiprocess environment
    env = make_vec_env('FractionArith-v0', n_envs=1)
    model = PPO2(MlpPolicy, env, verbose=1,
            gamma=0.5,
            tensorboard_log="./ppo_FractionArith-v0/")

    while True:
        model.learn(total_timesteps=9999999999)
        # model.save("ppo2_cartpole")

        # del model # remove to demonstrate saving and loading

        # model = PPO2.load("ppo2_cartpole")

        # Enjoy trained agent
        # obs = env.reset()
        # rwd = 0
        # for _ in range(100):
        #     action, _states = model.predict(obs)
        #     obs, rewards, dones, info = env.step(action)
        #     rwd += np.sum(rewards)
        #     env.render()
        # print(rwd)
