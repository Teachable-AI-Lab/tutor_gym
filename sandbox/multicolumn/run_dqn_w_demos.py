import numpy as np
import gym
from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy

from tutorenvs.utils import MultiDiscreteToDiscreteWrapper
from tutorenvs.multicolumn import MultiColumnAdditionDigitsEnv
import os
# from stable_baselines.common.cmd_util import make_vec_env

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from stable_baselines3.common import logger
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.noise import ActionNoise
from stable_baselines3.common.policies import BasePolicy
from stable_baselines3.common.save_util import load_from_pkl, save_to_pkl
from stable_baselines3.common.type_aliases import GymEnv, MaybeCallback, RolloutReturn
from stable_baselines3.common.utils import safe_mean
from stable_baselines3.common.vec_env import VecEnv

class DQN_w_Demos(DQN):
    def __init__(self,policy, env, max_incorrect=5, **kwargs):
        self.max_incorrect = max_incorrect
        super(DQN_w_Demos, self).__init__(policy, env,**kwargs)



    def collect_rollouts(
            self,
            env: VecEnv,
            callback: BaseCallback,
            n_episodes: int = 1,
            n_steps: int = -1,
            action_noise: Optional[ActionNoise] = None,
            learning_starts: int = 0,
            replay_buffer: Optional[ReplayBuffer] = None,
            log_interval: Optional[int] = None,
        ) -> RolloutReturn:
            """
            Collect experiences and store them into a ReplayBuffer.

            :param env: The training environment
            :param callback: Callback that will be called at each step
                (and at the beginning and end of the rollout)
            :param n_episodes: Number of episodes to use to collect rollout data
                You can also specify a ``n_steps`` instead
            :param n_steps: Number of steps to use to collect rollout data
                You can also specify a ``n_episodes`` instead.
            :param action_noise: Action noise that will be used for exploration
                Required for deterministic policy (e.g. TD3). This can also be used
                in addition to the stochastic policy for SAC.
            :param learning_starts: Number of steps before learning for the warm-up phase.
            :param replay_buffer:
            :param log_interval: Log data every ``log_interval`` episodes
            :return:
            """
            episode_rewards, total_timesteps = [], []
            total_steps, total_episodes = 0, 0

            assert isinstance(env, VecEnv), "You must pass a VecEnv"
            assert env.num_envs == 1, "OffPolicyAlgorithm only support single environment"

            if self.use_sde:
                self.actor.reset_noise()

            callback.on_rollout_start()
            continue_training = True

            while total_steps < n_steps or total_episodes < n_episodes:
                done = False
                episode_reward, episode_timesteps = 0.0, 0
                
                n_incorrect = 0

                while not done:
                    # print("START", n_incorrect)
                    if self.use_sde and self.sde_sample_freq > 0 and total_steps % self.sde_sample_freq == 0:
                        # Sample a new noise matrix
                        self.actor.reset_noise()


                    if(n_incorrect < self.max_incorrect):
                    # Select action randomly or according to policy
                        # print("n_incorrect: ",n_incorrect)
                        action, buffer_action = self._sample_action(learning_starts, action_noise)
                        # print(action)
                    else:
                        # print(env.__dict__)
                        action = buffer_action =  env.envs[0].request_demo_encoded()
                        n_incorrect = 0
                        # print("DEMO: ",action)

                    # Rescale and perform action
                    new_obs, reward, done, infos = env.step(action)
                    # print(reward[0], reward[0] < 0, done)
                    if(reward[0] < 0): n_incorrect += 1
                    if(done): n_incorrect = 0
                    # print(n_incorrect, self.max_incorrect)

                    self.num_timesteps += 1
                    episode_timesteps += 1
                    total_steps += 1

                    # Give access to local variables
                    callback.update_locals(locals())
                    # Only stop training if return value is False, not when it is None.
                    if callback.on_step() is False:
                        return RolloutReturn(0.0, total_steps, total_episodes, continue_training=False)

                    episode_reward += reward

                    # Retrieve reward and episode length if using Monitor wrapper
                    self._update_info_buffer(infos, done)

                    # Store data in replay buffer
                    if replay_buffer is not None:
                        # Store only the unnormalized version
                        if self._vec_normalize_env is not None:
                            new_obs_ = self._vec_normalize_env.get_original_obs()
                            reward_ = self._vec_normalize_env.get_original_reward()
                        else:
                            # Avoid changing the original ones
                            self._last_original_obs, new_obs_, reward_ = self._last_obs, new_obs, reward

                        replay_buffer.add(self._last_original_obs, new_obs_, buffer_action, reward_, done)

                    self._last_obs = new_obs
                    # Save the unnormalized observation
                    if self._vec_normalize_env is not None:
                        self._last_original_obs = new_obs_

                    self._update_current_progress_remaining(self.num_timesteps, self._total_timesteps)

                    # For DQN, check if the target network should be updated
                    # and update the exploration schedule
                    # For SAC/TD3, the update is done as the same time as the gradient update
                    # see https://github.com/hill-a/stable-baselines/issues/900
                    self._on_step()

                    if 0 < n_steps <= total_steps:
                        print("BREAK", n_steps, total_steps)
                        break

                if done:
                    total_episodes += 1
                    self._episode_num += 1
                    episode_rewards.append(episode_reward)
                    total_timesteps.append(episode_timesteps)

                    if action_noise is not None:
                        action_noise.reset()

                    # Log training infos
                    if log_interval is not None and self._episode_num % log_interval == 0:
                        self._dump_logs()

            mean_reward = np.mean(episode_rewards) if total_episodes > 0 else 0.0

            callback.on_rollout_end()

            return RolloutReturn(mean_reward, total_steps, total_episodes, continue_training)



if __name__ == "__main__":
    for i in range(10):
        os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
        # multiprocess environment
        env = gym.make('MulticolumnArithSymbolic-v0')
        env = MultiDiscreteToDiscreteWrapper(env)
        # env = make_vec_env('MultiColumnArith-v0', n_envs=1)
        # env = MultiDiscreteToDiscreteWrapper(MultiColumnAdditionDigitsEnv())
        model = DQN_w_Demos(MlpPolicy, env, 
                    max_incorrect=1,
                    verbose=1,
                    learning_rate=0.0005,
                    batch_size=256,
                    train_freq=-1,
                    n_episodes_rollout=1,
                    exploration_fraction=0.1,
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
