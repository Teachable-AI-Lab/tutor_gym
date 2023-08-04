import numpy as np
import gym
from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy

from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
import os

if __name__ == "__main__":
    os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
    # multiprocess environment
    env = gym.make('MulticolumnArithSymbolic-v0')
    env = MultiDiscreteToDiscreteWrapper(env)
    model = DQN(MlpPolicy, env, verbose=1,
                learning_rate=0.0005,
                batch_size=256,
                train_freq=1,
                exploration_fraction=0.2,
                exploration_initial_eps=0.45,
                exploration_final_eps=0.0,
                gamma=0.0,
                learning_starts=1,
                policy_kwargs={'net_arch': [200, 200, 200]}, # {'qf': [65], 'pi': [65]}]},
                tensorboard_log="./tensorboard_dqn_multi/"
                )
            # gamma=0.1,
            # tensorboard_log="./tensorboard/v0/")


    # while True:
    model.learn(total_timesteps=30000000)
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
