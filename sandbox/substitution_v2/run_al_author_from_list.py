"""Author-training harness that uses only curated substitution problems."""

from __future__ import annotations

import argparse
import json
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


DEFAULT_PROBLEM_FILE = Path(__file__).with_name("problem_list.json")


def make_agent() -> CREAgent:

    agent_args = {
        "function_set": ["Multiply", "Add"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 4,
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


def load_problems(path: Path) -> list[dict]:

    with path.open() as problem_file:
        data = json.load(problem_file)

    if not isinstance(data, list):
        raise ValueError("Problem file must contain a JSON list of problems")

    problems: list[dict] = []
    for problem in data:
        if not isinstance(problem, dict):
            raise ValueError("Each entry in the problem list must be a JSON object")
        problems.append(problem)

    return problems


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    problem_path = Path(args.problem_list)
    problems = load_problems(problem_path)

    env = SubstitutionTutorV2(
        problems=problems,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    log_dir = Path("log_substitution_v2_author")
    logger = DataShopLogger(
        f"substitution_v2_{args.agent_type}_{len(problems)}probs_curated",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=problems,
        n_problems=len(problems),
    )

    print(
        Fore.CYAN
        + "Running curated problem list"
        + f" ({len(problems)} problems from {problem_path})..."
    )
    trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train DIPL on substitution v2 curated problems only"
    )
    parser.add_argument(
        "--problem-list",
        default=str(DEFAULT_PROBLEM_FILE),
        help="Path to JSON file containing an array of substitution problems",
    )
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)