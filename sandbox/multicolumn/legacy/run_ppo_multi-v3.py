import gym
from stable_baselines3 import PPO
from stable_baselines3.ppo import CnnPolicy
# from stable_baselines3.ppo import MlpPolicy
from stable_baselines3.common import make_vec_env
# from stable_baselines3 import DQN
# from stable_baselines3.dqn import CnnPolicy
import tutorenvs
import numpy as np


if __name__ == "__main__":

    # multiprocess environment
    env = make_vec_env('MultiColumnArith-v3', n_envs=1)
    model = PPO(CnnPolicy, env, verbose=1,
            gamma=0.9,
            policy_kwargs={'net_arch': [65, 65, {'vf': [65], 'pi': [65]}]},
            tensorboard_log="./tensorboard/v3/")

    # env = make_vec_env('MultiColumnArith-v3', n_envs=1)
    # model = DQN(CnnPolicy, env, verbose=1,
    #         gamma=0.8,
    #         # exploration_fraction=.0,
    #         # exploration_final_eps=0.3,
    #         # prioritized_replay=True,
    #         # policy_kwargs={'layers': [64, 64, 64]},
    #         # policy_kwargs={'net_arch': [65, 65, {'vf': [65], 'pi': [65]}]},
    #         tensorboard_log="./tensorboard/v3/")

    # model = PPO.load('multi-v3')

    while True:
        model.learn(total_timesteps=100)
        model.save('multi-v3')

        # To demonstrate saving and loading
        # model.save("ppo2_multicolumn-v0")
        # del model
        # model = PPO2.load("ppo2_multicolumn-v0")

        # Enjoy trained agent
        obs = env.reset()
        rwd = 0
        for _ in range(3000000):
            action, _states = model.predict(obs)
            obs, rewards, dones, info = env.step(action)
            rwd += np.sum(rewards)
            env.render()
        print(rwd)
