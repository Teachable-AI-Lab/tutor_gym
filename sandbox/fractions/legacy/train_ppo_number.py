from typing import Dict
from typing import Any

import optuna
from torch import nn as nn
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import VecEnv

from tutorenvs.utils import linear_schedule


def get_args(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sampler for PPO hyperparams.
    :param trial:
    :return:
    """
    batch_size = int(2**params['batches_pow'])
    n_steps = int(2**params['n_step_pow'])
    gamma = params['gamma']
    learning_rate = params['lr']
    lr_schedule = params['lr_schedule']
    ent_coef = params['ent_coef']
    clip_range = params['clip_range']
    n_epochs = params['n_epochs']
    gae_lambda = params['gae_lambda']
    max_grad_norm = params['max_grad_norm']
    vf_coef = params['vf_coef']
    net_arch = params['net_arch']
    shared_arch = params['shared_arch']
    activation_fn = params['activation_fn']

    # TODO: account when using multiple envs
    if batch_size > n_steps:
        batch_size = n_steps

    if lr_schedule == "linear":
        learning_rate = linear_schedule(learning_rate)

    # Independent networks usually work best
    # when not working with images
    net_arch = {
        True: {
            "tiny": [32, dict(pi=[32], vf=[32])],
            "small": [64, dict(pi=[64], vf=[64])],
            "medium": [128, dict(pi=[128], vf=[128])],
        },
        False: {
            "tiny": [dict(pi=[32, 32], vf=[32, 32])],
            "small": [dict(pi=[64, 64], vf=[64, 64])],
            "medium": [dict(pi=[128, 128], vf=[128, 128])],
        }
    }[shared_arch][net_arch]

    activation_fn = {
        "tanh": nn.Tanh,
        "relu": nn.ReLU,
        "elu": nn.ELU,
        "leaky_relu": nn.LeakyReLU
    }[activation_fn]

    ortho_init = False

    return {
        "n_steps":
        n_steps,
        "batch_size":
        batch_size,
        "gamma":
        gamma,
        "learning_rate":
        learning_rate,
        "ent_coef":
        ent_coef,
        "clip_range":
        clip_range,
        "n_epochs":
        n_epochs,
        "gae_lambda":
        gae_lambda,
        "max_grad_norm":
        max_grad_norm,
        "vf_coef":
        vf_coef,
        # "sde_sample_freq": sde_sample_freq,
        "policy_kwargs":
        dict(
            # log_std_init=log_std_init,
            net_arch=net_arch,
            activation_fn=activation_fn,
            ortho_init=ortho_init,
        ),
    }


class TrialEvalCallback(EvalCallback):
    """
    Callback used for evaluating and reporting a trial.
    """
    def __init__(
        self,
        eval_env: VecEnv,
        trial: optuna.Trial,
        n_eval_episodes: int = 5,
        eval_freq: int = 10000,
        deterministic: bool = True,
        verbose: int = 0,
    ):

        super(TrialEvalCallback, self).__init__(
            eval_env=eval_env,
            n_eval_episodes=n_eval_episodes,
            eval_freq=eval_freq,
            deterministic=deterministic,
            verbose=verbose,
        )
        self.trial = trial
        self.eval_idx = 0
        self.is_pruned = False

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            super(TrialEvalCallback, self)._on_step()
            self.eval_idx += 1
            # report best or report current ?
            # report num_timesteps or elasped time ?
            self.trial.report(self.last_mean_reward, self.eval_idx)
            # Prune trial if need
            if self.trial.should_prune():
                self.is_pruned = True
                return False
        return True


if __name__ == "__main__":

    params = {'activation_fn': 'relu', 'batches_pow': 9.0, 'clip_range': 0.2,
              'ent_coef': 0.013748019113722395, 'gae_lambda': 0.99, 'gamma':
              0.0, 'lr': 0.005533935261484844, 'lr_schedule': 'linear',
              'max_grad_norm': 2, 'n_epochs': 5, 'n_step_pow': 9.0, 'net_arch':
              'small', 'shared_arch': False, 'vf_coef': 0.5470657324084635}

    kwargs = get_args(params)

    # multiprocess environment
    env = make_vec_env('FractionArith-v0', n_envs=1)
    model = PPO(
        MlpPolicy,
        env,
        verbose=1,
        tensorboard_log="./tensorboard_ppo/",
        **kwargs
    )
    # gamma=0.1,
    # tensorboard_log="./tensorboard/v0/")

    # while True:
    # Train
    model.learn(total_timesteps=1000000)

    # Test
    # obs = env.reset()
    # rwd = 0
    # for _ in range(10000):
    #     action, _states = model.predict(obs)
    #     obs, rewards, dones, info = env.step(action)
    #     rwd += np.sum(rewards)
    #     env.render()
    # print(rwd)
