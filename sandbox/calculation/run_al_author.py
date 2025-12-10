"""Author-training harness for the CalculationTutor environment."""

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
from tutorgym.env_classes.misc.calculation.calculation import CalculationTutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)

CURATED_PROBLEMS = [
    {
        "equation_tokens": [
            "t",
            "=",
            "(",
            "(",
            "2.5",
            "*",
            "6",
            ")",
            "*",
            "(",
            "500",
            "*",
            "5",
            "*",
            "20",
            ")",
            ")",
            "-",
            "(",
            "6",
            "*",
            "(",
            "500",
            "*",
            "5",
            "*",
            "20",
            ")",
            ")",
            "-",
            "2000",
        ],
        "unknown": "t",
    },
    {
        "equation_tokens": [
            "M",
            "+",
            "18",
            "+",
            "2",
            "*",
            "18",
            "+",
            "2/5",
            "*",
            "150",
            "=",
            "150",
        ],
        "unknown": "M",
    },
]

INT_MIN, INT_MAX = 1, 200


def make_agent() -> CREAgent:

    agent_args = {
        "function_set": ["Multiply", "Add", "Divide", "Subtract"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 2,
        "where_learner": "mostspecific",
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


def _is_numeric_token(token: str) -> bool:
    if any(char.isalpha() for char in token):
        return False

    allowed_chars = set("0123456789./")
    if not token or any(ch not in allowed_chars for ch in token):
        return False
    if token in {"/", "."}:
        return False
    if token.count("/") > 1 or token.count(".") > 1:
        return False
    if token[0] in {"/", "."} or token[-1] in {"/", "."}:
        return False
    return True


def _mutate_token(token: str, rng: random.Random) -> str:
    if not _is_numeric_token(token):
        return token

    if "/" in token:
        numerator_digits = len(token.split("/")[0])
        denominator_digits = len(token.split("/")[1])
        numerator = rng.randint(INT_MIN, INT_MAX)
        denominator = rng.randint(INT_MIN, INT_MAX)
        numerator_fmt = f"{numerator:0{numerator_digits}d}" if numerator_digits > 1 else str(numerator)
        denominator_fmt = (
            f"{denominator:0{denominator_digits}d}" if denominator_digits > 1 else str(denominator)
        )
        return f"{numerator_fmt}/{denominator_fmt}"

    if "." in token:
        decimals = len(token.split(".")[1])
        value = round(rng.uniform(float(INT_MIN), float(INT_MAX)), decimals)
        return f"{value:.{decimals}f}"

    return str(rng.randint(INT_MIN, INT_MAX))


def _make_variation(problem: dict, variant_index: int, rng: random.Random) -> dict:
    variant_tokens = [_mutate_token(token, rng) for token in problem["equation_tokens"]]
    base_index = problem.get("problem_index", 1)
    return {
        "equation_tokens": variant_tokens,
        "unknown": problem["unknown"],
        "problem_index": base_index,
        "variant_index": variant_index,
    }


def build_problem_sequence(base_problem: dict, n_variations: int, seed: int) -> list[dict]:

    rng = random.Random(seed)
    sequence = [
        {
            **base_problem,
            "problem_index": base_problem.get("problem_index", 1),
            "variant_index": 0,
        }
    ]

    for variant_index in range(1, n_variations + 1):
        sequence.append(_make_variation(base_problem, variant_index, rng))

    return sequence


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    base_idx = max(1, min(args.base_problem_index, len(CURATED_PROBLEMS)))
    base_problem = CURATED_PROBLEMS[base_idx - 1]

    env = CalculationTutor(
        problems=[base_problem],
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    problem_sequence = build_problem_sequence(base_problem, args.n_variations, args.seed)
    total_problems = len(problem_sequence)

    log_dir = Path("log_calculation_author")
    logger = DataShopLogger(
        f"calculation_{args.agent_type}_{total_problems}probs",
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
        + f"Running base problem #{base_idx} plus {args.n_variations} variations ({total_problems} total)..."
    )
    trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train DIPL on one calculation problem and its numeric variations"
    )
    parser.add_argument("--n-variations", type=int, default=300)
    parser.add_argument("--base-problem-index", type=int, default=1)
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    faulthandler.enable()
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)