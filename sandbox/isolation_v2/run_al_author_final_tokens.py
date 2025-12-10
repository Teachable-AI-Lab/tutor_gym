from __future__ import annotations

import argparse
import faulthandler
import json
import random
import sys
from pathlib import Path
from typing import List, Sequence

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


DEFAULT_ADDITIONAL_MANIFEST = "final_tokens_unknowns_as_x(test).json"

DEFAULT_ADDITIONAL_LIMIT: int | None = None


def make_agent() -> CREAgent:

    agent_args = {
        "function_set": ["Multiply", "Add"],
        "feature_set": ["Equals"],
        "planner": "set_chaining",
        "explanation_choice": "least_operations",
        "search_depth": 10,
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


def _infer_unknown_from_tokens(tokens: Sequence[str], idx: int) -> str:

    for token in tokens:
        if any(ch.isalpha() for ch in token):
            return token
    raise ValueError(f"Entry #{idx} is missing an unknown and none could be inferred")


def load_problem_manifest(
    manifest_path: Path, description: str, *, include_variant_index: bool
) -> List[dict]:

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Expected {description} at {manifest_path}; none found."
        )

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        problems = data.get("problems")
    else:
        problems = data

    if not isinstance(problems, list):
        raise ValueError(f"{description} must contain a list of problems")

    normalised: List[dict] = []
    for idx, entry in enumerate(problems, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry #{idx} is not an object: {entry!r}")

        tokens = entry.get("equation_tokens") or entry.get("final_tokens")
        unknown = entry.get("unknown")

        if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
            raise ValueError(
                f"Entry #{idx} has invalid equation_tokens/final_tokens: {tokens!r}"
            )

        if not isinstance(unknown, str):
            unknown = _infer_unknown_from_tokens(tokens, idx)

        problem_index = entry.get("problem_index", idx)
        variant_index = entry.get("variant_index", 0) if include_variant_index else 0

        normalised.append(
            {
                "equation_tokens": tokens,
                "unknown": unknown,
                "problem_index": problem_index,
                "variant_index": variant_index,
            }
        )

    if not normalised:
        raise ValueError(f"{description} did not provide any problems")

    return normalised


def build_problem_sequence(problems: Sequence[dict], n_problems: int) -> List[dict]:

    if n_problems > len(problems):
        raise ValueError(
            "Requested more problems than available in the manifest"
            f" (requested {n_problems}, available {len(problems)})"
        )
    return list(problems[:n_problems])


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    manifest_path = Path(__file__).with_name("whole_problem_tokens.json")
    manifest_problems = load_problem_manifest(
        manifest_path, "whole_problem_tokens.json", include_variant_index=True
    )

    n_problems = args.n_problems or len(manifest_problems)
    primary_env = IsolationTutorV2(
        problems=manifest_problems,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )
    primary_sequence = build_problem_sequence(manifest_problems, n_problems)

    log_dir = Path("log_isolation_v2_author_final_tokens")
    primary_logger = DataShopLogger(
        f"isolation_v2_finaltokens_{args.agent_type}_{n_problems}probs",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    primary_trainer = AuthorTrainer(
        agent,
        primary_env,
        logger=primary_logger,
        problem_set=primary_sequence,
        n_problems=n_problems,
    )

    print(Fore.CYAN + f"Running {n_problems} final-token problems...")
    primary_trainer.start()

    additional_manifest_path = Path(args.additional_manifest or DEFAULT_ADDITIONAL_MANIFEST)
    if not additional_manifest_path.is_absolute():
        additional_manifest_path = Path(__file__).with_name(args.additional_manifest)

    additional_problems = load_problem_manifest(
        additional_manifest_path,
        additional_manifest_path.name,
        include_variant_index=False,
    )
    additional_limit = args.additional_limit
    if additional_limit is None:
        additional_limit = DEFAULT_ADDITIONAL_LIMIT

    n_additional = additional_limit or len(additional_problems)
    additional_sequence = build_problem_sequence(additional_problems, n_additional)

    additional_env = IsolationTutorV2(
        problems=additional_problems,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    additional_log_dir = log_dir / "additional"
    additional_logger = DataShopLogger(
        f"isolation_v2_additional_{args.agent_type}_{n_additional}probs",
        extra_kcs=["field"],
        output_dir=str(additional_log_dir),
    )

    additional_trainer = AuthorTrainer(
        agent,
        additional_env,
        logger=additional_logger,
        problem_set=additional_sequence,
        n_problems=n_additional,
    )

    print(
        Fore.MAGENTA
        + f"Running {n_additional} additional final-token problems from {additional_manifest_path.name}..."
    )
    additional_trainer.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train DIPL on isolation V2 final-token problems with optional"
            " additional training from another manifest"
        )
    )
    parser.add_argument("--n-problems", type=int, default=None)
    parser.add_argument("--additional-manifest", default=DEFAULT_ADDITIONAL_MANIFEST)
    parser.add_argument(
        "--additional-limit",
        type=int,
        default=None,
        help=(
            "Cap the number of additional problems used after the whole-problem"
            " manifest; defaults to the full additional manifest when omitted."
        ),
    )
    parser.add_argument("--agent-type", default="DIPL")
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    faulthandler.enable()
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)
