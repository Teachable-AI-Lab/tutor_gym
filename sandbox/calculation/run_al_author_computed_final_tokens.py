"""Author-training harness for CalculationTutor using computed final tokens."""

from __future__ import annotations

import argparse
import faulthandler
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT_DIR = Path(__file__).resolve().parent

import colorama
from colorama import Fore

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers  
from tutorgym.env_classes.misc.calculation.calculation import CalculationTutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)

COMPUTED_TOKENS_PATH = SCRIPT_DIR / "computed_final_tokens.json"


def make_agent() -> CREAgent:

    agent_args = {
        "function_set": ["Multiply", "Add"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 5,
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


def load_computed_problems(path: Path = COMPUTED_TOKENS_PATH) -> List[Dict[str, Sequence[str]]]:

    if not path.exists():
        raise FileNotFoundError(
            "Expected computed_final_tokens.json to reside alongside the runner script"
        )

    data = path.read_text(encoding="utf-8")
    entries = json.loads(data)
    if not isinstance(entries, list):
        raise ValueError("computed_final_tokens.json must contain a list of entries")

    problems: List[Dict[str, Sequence[str]]] = []
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry #{idx} is not an object: {entry!r}")
        tokens = entry.get("final_tokens")
        if not isinstance(tokens, list) or not all(isinstance(tok, str) for tok in tokens):
            raise ValueError(
                f"Entry #{idx} has an invalid 'final_tokens' payload: {tokens!r}"
            )
        unknown = entry.get("unknown")
        if not unknown or not isinstance(unknown, str):
            raise ValueError(f"Entry #{idx} must specify an 'unknown' string")

        problems.append(
            {
                "equation_tokens": list(tokens),
                "unknown": unknown,
                "problem_index": entry.get("problem_index", idx),
            }
        )

    if not problems:
        raise ValueError("computed_final_tokens.json did not define any problems")

    return problems


def build_problem_sequence(
    problems: List[Dict[str, Sequence[str]]], n_problems: int | None
) -> List[Dict[str, Sequence[str]]]:

    total = len(problems)
    if n_problems is None:
        return problems
    if n_problems <= 0:
        raise ValueError("n_problems must be positive when provided")
    if n_problems > total:
        raise ValueError(
            "Requested more problems than available in computed_final_tokens.json"
            f" (requested {n_problems}, available {total})"
        )
    return problems[:n_problems]


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    manifest_path = SCRIPT_DIR / "computed_final_tokens.json"
    manifest_problems = load_computed_problems(manifest_path)
    env = CalculationTutor(
        problems=manifest_problems,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    problem_sequence = build_problem_sequence(manifest_problems, args.n_problems)

    n_selected = len(problem_sequence)
    log_dir = Path("log_calculation_author_computed_final_tokens")
    logger = DataShopLogger(
        f"calculation_computedtokens_{args.agent_type}_{n_selected}probs",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=problem_sequence,
        n_problems=n_selected,
    )

    print(Fore.CYAN + f"Running {n_selected} computed-final-token problems...")
    trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train DIPL on CalculationTutor problems from computed_final_tokens.json"
    )
    parser.add_argument("--n-problems", type=int, default=None)
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    faulthandler.enable()
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)