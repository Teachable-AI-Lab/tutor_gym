from typing import Dict
from typing import Any
import tempfile

import gym
import optuna
from torch import nn as nn
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy
# from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv
# from stable_baselines3.common.vec_env import VecEnv
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.monitor import load_results

import tutorenvs  # noqa: F401
from tutorenvs.utils import linear_schedule


def sample_ppo_params(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Sampler for PPO hyperparams.

    :param trial:
    :return:
    """
    n_step_pow = trial.suggest_discrete_uniform('n_step_pow', 3, 11, 1)
    n_steps = int(2**n_step_pow)

    # possible_n_steps = [8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    # n_steps = trial.suggest_categorical("n_steps",
    #                                     possible_n_steps)

    batches_pow = trial.suggest_discrete_uniform('batches_pow', 3,
                                                 n_step_pow, 1)
    batch_size = int(2**batches_pow)

    # possible_batches = [8, 16, 32, 64, 128, 256, 512]
    # batch_size = trial.suggest_categorical("batch_size",
    #                                        possible_batches)

    gamma = trial.suggest_categorical("gamma", [0.0])
    # 0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    learning_rate = trial.suggest_loguniform("lr", 1e-8, 1)
    # lr_schedule = "constant"
    # Uncomment to enable learning rate schedule
    lr_schedule = trial.suggest_categorical('lr_schedule',
                                            ['linear', 'constant'])
    ent_coef = trial.suggest_loguniform("ent_coef", 0.00000000001, 0.1)
    clip_range = trial.suggest_categorical("clip_range",
                                           [0.05, 0.1, 0.2, 0.3, 0.4])
    n_epochs = trial.suggest_categorical("n_epochs", [1, 5, 10, 20])
    gae_lambda = trial.suggest_categorical(
        "gae_lambda", [0.8, 0.9, 0.92, 0.95, 0.98, 0.99, 1.0])
    max_grad_norm = trial.suggest_categorical(
        "max_grad_norm", [0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 5])
    vf_coef = trial.suggest_uniform("vf_coef", 0, 1)
    net_arch = trial.suggest_categorical("net_arch",
                                         ["tiny", "small", "medium"])
    shared_arch = trial.suggest_categorical("shared_arch", [True, False])
    ortho_init = False
    activation_fn = trial.suggest_categorical("activation_fn",
                                              ["tanh", "relu"])

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


class TrialCallback(BaseCallback):
    """
    Callback used for evaluating and reporting a trial.
    """
    def __init__(
        self,
        trial: optuna.Trial,
        log_dir: str,
        n_eval_episodes: int = 10,
        eval_freq: int = 10000,
        min_eval: float = -1000,
        verbose: int = 0,
    ):
        super(TrialCallback, self).__init__(verbose)

        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.log_dir = log_dir
        self.trial = trial
        self.eval_idx = 0
        self.is_pruned = False
        self.min_eval = min_eval

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            results = load_results(self.log_dir)
            if len(results) < self.n_eval_episodes:
                return True
            avg_last_n = results['r'][-self.n_eval_episodes:].mean()
            self.eval_idx += 1
            # report best or report current ?
            # report num_timesteps or elasped time ?
            self.trial.report(avg_last_n, self.eval_idx)
            # print('Idx:', self.eval_idx, 'Avg_last_n', avg_last_n)

            # Prune trial if need
            if avg_last_n < self.min_eval or self.trial.should_prune():
                self.is_pruned = True
                return False

        return True


def objective(trial: optuna.Trial) -> float:
    n_eval_episodes = 15
    eval_freq = 5000
    n_steps = 350000

    with tempfile.TemporaryDirectory() as log_dir:
        env = DummyVecEnv([
            lambda: Monitor(gym.make('MulticolumnArithSymbolic-v1'), log_dir)])

        ppo_args = sample_ppo_params(trial)

        model = PPO(MlpPolicy, env,
                    # tensorboard_log="./tensorboard_ppo_multi/",
                    **ppo_args)
        # gamma=0.1,
        # tensorboard_log="./tensorboard/v0/")
        callback = TrialCallback(trial, log_dir, verbose=1,
                                 n_eval_episodes=n_eval_episodes,
                                 eval_freq=eval_freq)

        try:
            model.learn(total_timesteps=n_steps, callback=callback)
            model.env.close()
        except Exception as e:
            model.env.close()
            print(e)
            raise optuna.exceptions.TrialPruned()

        is_pruned = callback.is_pruned
        del model.env
        del model

        if is_pruned:
            raise optuna.exceptions.TrialPruned()

        results = load_results(log_dir)
        avg_last_n = results['r'][-n_eval_episodes:].mean()
        # print('Final avg_last_n:', avg_last_n)
        return avg_last_n


if __name__ == "__main__":

    # multiprocess environment
    # env = make_vec_env('MulticolumnArithSymbolic-v0', n_envs=1)

    pruner = optuna.pruners.MedianPruner(n_warmup_steps=20000)

    study = optuna.create_study(study_name="ppo-multicolumn-operator",
                                pruner=pruner,
                                direction="maximize",
                                storage='sqlite:///study.db',
                                load_if_exists=True
                                )
    try:
        study.optimize(objective, n_trials=1000, n_jobs=1)
    except Exception as e:
        print(e)
    finally:
        print("BEST")
        print(study.best_params)
