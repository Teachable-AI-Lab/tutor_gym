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
    # params = {
    #     'batch_size': 32,
    #     'n_steps': 16,
    #     'gamma': 0.0,
    #     'lr': 0.00017980950834568327,
    #     'lr_schedule': 'constant',
    #     'ent_coef': 0.07439893598338435,
    #     'clip_range': 0.4,
    #     'n_epochs': 10,
    #     'gae_lambda': 0.95,
    #     'max_grad_norm': 0.8,
    #     'vf_coef': 0.13214811411452415,
    #     'net_arch': 'medium',
    #     'shared_arch': False,
    #     'activation_fn': 'tanh'
    # }

    # params = {'activation_fn': 'relu', 'batch_size': 32, 'clip_range': 0.1,
    #           'ent_coef': 0.008425259906148678, 'gae_lambda': 0.98, 'gamma':
    #           0.0, 'lr': 0.0014548935455020253, 'lr_schedule': 'linear',
    #           'max_grad_norm': 0.6, 'n_epochs': 5, 'n_steps': 64, 'net_arch':
    #           'medium', 'shared_arch': True, 'vf_coef': 0.6725952403531438}

    params = {'n_step_pow': 5.0, 'batches_pow': 5.0, 'gamma': 0.0, 'lr':
              0.0014291278312354846, 'lr_schedule': 'linear', 'ent_coef':
              0.042102094710275415, 'clip_range': 0.2, 'n_epochs': 5,
              'gae_lambda': 0.92, 'max_grad_norm': 0.7, 'vf_coef':
              0.40158288555773314, 'net_arch': 'medium', 'shared_arch': False,
              'activation_fn': 'relu'}

    kwargs = get_args(params)

    # multiprocess environment
    env = make_vec_env('MulticolumnArithSymbolic-v0', n_envs=1)
    model = PPO(
        MlpPolicy,
        env,
        verbose=1,
        tensorboard_log="./tensorboard_ppo_multi/",
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
