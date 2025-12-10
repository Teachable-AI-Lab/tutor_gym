"""Author-training harness for the IsolationTutorV2 environment."""

from __future__ import annotations

import argparse
import faulthandler
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import colorama
from colorama import Fore

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers  
from tutorgym.env_classes.misc.isolation_v2.isolation_v2 import IsolationTutorV2
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)

CURATED_PROBLEMS = [
    {
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    },{
                "equation_tokens": [
                    "S",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
    }
]


def make_agent() -> CREAgent:
    """Return a CREAgent configured like the original isolation author runner."""

    agent_args = {
        "function_set": ["Multiply", "Add"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 2,
        "when_learner": "stand",
        "which_learner": "when_prediction",
        "action_chooser": "max_which_utility",
        "suggest_uncert_neg": True,
        "error_on_bottom_out": False,
        "one_skill_per_match": True,
        "extra_features": ["Match"],
        "should_find_neighbors": True,
        "when_args": {
            "encode_relative": False,
            "check_sanity": False,
        },
        "process_learner": "htnlearner",
        "track_rollout_preseqs": True,
        "action_filter_args": {"thresholds": [0.3, 0, -0.5, -0.75]},
    }
    return CREAgent(**agent_args)


def build_problem_sequence(env: IsolationTutorV2, n_problems: int) -> list[dict]:

    problems = list(CURATED_PROBLEMS)
    while len(problems) < n_problems:
        problems.append(env.generate_random_problem())
    return problems[:n_problems]


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    env = IsolationTutorV2(
        problems=CURATED_PROBLEMS,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    problem_sequence = build_problem_sequence(env, args.n_problems)

    log_dir = Path("log_isolation_v2_author")
    logger = DataShopLogger(
        f"isolation_v2_{args.agent_type}_{args.n_problems}probs",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=problem_sequence,
        n_problems=args.n_problems,
    )

    print(Fore.CYAN + f"Running {args.n_problems} problems...")
    trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train DIPL on isolation V2 only")
    parser.add_argument("--n-problems", type=int, default=5)
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    faulthandler.enable()
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)