"""Author-training harness for the substitution tutor."""

from __future__ import annotations

import argparse
import faulthandler
import random
from pathlib import Path

import colorama
from colorama import Fore

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers 
from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)


CURATED_PROBLEMS = [
    {
        "variables": ["M", "P", "G", "B", "W"],
        "quantities": {"W": "150", "P": "18"},
        "relationships": [
            "G = 2 * P",
            "B = 2/5 * W",
            "M + P + G + B = W",
        ],
        "unknowns": ["M"],
    },
    {
        "variables": ["S", "D", "T"],
        "quantities": {"D": "42"},
        "relationships": [
            "T = 3 * D",
            "S + T = 5 * D",
        ],
        "unknowns": ["S"],
    },
    {
        "variables": ["W", "E", "T"],
        "quantities": {"E": "12", "T": "50/60"},
        "relationships": [
            "W = E * T",
        ],
        "unknowns": ["W"],
    },
    {"variables": ["C1","C2","C3","F1","F2","F3","V1","V2","V3","T"],
 "quantities": {"C1": "7000", "C2": "5000", "C3": "3000", "F1": "3/4", "F2": "4/5", "F3": "1/2"},
 "relationships": ["V1 = F1 * C1", "V2 = F2 * C2", "V3 = F3 * C3", "T = V1 + V2 + V3"],
 "unknowns": ["T"]}
]


def make_agent() -> CREAgent:

    agent_args = {
        "function_set": ["Multiply", "Add"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 2,
        "where_learner" : "antiunify",
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


def build_problem_sequence(env: SubstitutionTutorV2, n_problems: int) -> list[dict]:

    problems: list[dict] = []
    for _ in range(n_problems):
        problems.append(env.generate_random_problem())

    problems.extend(CURATED_PROBLEMS)
    return problems


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    env = SubstitutionTutorV2(
        problems=CURATED_PROBLEMS,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    problem_sequence = build_problem_sequence(env, args.n_problems)
    total_problems = len(problem_sequence)

    log_dir = Path("log_substitution_v2_author")
    logger = DataShopLogger(
        f"substitution_v2_{args.agent_type}_{args.n_problems}probs",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=problem_sequence,
        n_problems=total_problems,
    )

    print(
        Fore.CYAN
        + "Running "
        + f"{args.n_problems} training problems"
        + " + "
        + f"{len(CURATED_PROBLEMS)} curated checks"
        + f" = {total_problems} total..."
    )
    trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train DIPL on substitution v2 only")
    parser.add_argument("--n-problems", type=int, default=20)
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    faulthandler.enable()
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)