"""Train on one demo plus structural variations using substitution_v2."""

from __future__ import annotations

import argparse
import random
import string
import re
from typing import Dict, List

import colorama
from colorama import Fore, Style

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers 
from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)

# ---------------------------------------------------------------------------
# Fixed training example and variation generation controls
# ---------------------------------------------------------------------------
TRAINING_PROBLEM: Dict[str, object] = {
        "variables": [
            "p",
            "m",
            "t"
        ],
        "quantities": {
            "p": "8",
            "m": "20"
        },
        "relationships": [
            "120 / p * m = t * 60"
        ],
        "unknowns": [
            "t"
        ]
}

DEFAULT_RANDOM_SEED = 7

DEFAULT_RANDOM_TRAIN_COUNT =10


# ---------------------------------------------------------------------------
# Agent helpers
# ---------------------------------------------------------------------------
def make_agent() -> CREAgent:

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


# ---------------------------------------------------------------------------
# Problem helpers
# ---------------------------------------------------------------------------
_IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_NUMBER_RE = re.compile(r"\d+")


def _randomize_numeric_string(
    text: str, rng: random.Random, *, min_value: int = 40, max_value: int = 220
) -> str:

    number_map: Dict[str, str] = {}

    def repl_number(match: re.Match[str]) -> str:
        literal = match.group(0)
        if literal not in number_map:
            candidate = rng.randint(min_value, max_value)
            if str(candidate) == literal:
                candidate = rng.randint(min_value, max_value)
            number_map[literal] = str(candidate)
        return number_map[literal]

    return _NUMBER_RE.sub(repl_number, text)


def _remap_relationship(relationship: str, mapping: Dict[str, str], rng: random.Random) -> str:

    def repl_ident(match: re.Match[str]) -> str:
        ident = match.group(0)
        return mapping.get(ident, ident)

    remapped = _IDENTIFIER_RE.sub(repl_ident, relationship)
    return _randomize_numeric_string(remapped, rng, min_value=2, max_value=220)


def generate_variations(
    *, count: int, base: Dict[str, object], seed: int | None = None
) -> List[Dict[str, object]]:

    rng = random.Random(seed)
    letters = list(string.ascii_lowercase)

    base_vars = list(base["variables"])
    base_unknowns: List[str] = base["unknowns"] 
    for unknown in base_unknowns:
        if unknown not in base_vars:
            base_vars.append(unknown)

    base_quantities: Dict[str, str] = base["quantities"] 
    quantity_vars = list(base_quantities)
    mapping_keys = list(dict.fromkeys(base_vars + quantity_vars))
    base_relationships: List[str] = base["relationships"] 

    variations: List[Dict[str, object]] = []

    for _ in range(count):
        if len(mapping_keys) > len(letters):
            raise ValueError("Not enough unique letters available for remapping.")

        chosen = rng.sample(letters, len(mapping_keys))
        mapping = dict(zip(mapping_keys, chosen))

        variables = [mapping[v] for v in base_vars]
        quantities = {
            mapping[k]: _randomize_numeric_string(v, rng, min_value=40, max_value=220)
            for k, v in base_quantities.items()
        }
        relationships = [
            _remap_relationship(relationship, mapping, rng)
            for relationship in base_relationships
        ]
        unknowns = [mapping[u] for u in base_unknowns]

        variations.append(
            {
                "variables": variables,
                "quantities": quantities,
                "relationships": relationships,
                "unknowns": unknowns,
            }
        )

    return variations


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def run_training(args: argparse.Namespace) -> None:
    training_pool = [TRAINING_PROBLEM]
    if args.random_train_count:
        training_variations = generate_variations(
            count=args.random_train_count,
            base=TRAINING_PROBLEM,
            seed=args.seed + 1,
        )
        training_pool.extend(training_variations)

    env = SubstitutionTutorV2(
        problems=training_pool,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    logger = DataShopLogger(
        "substitution_v2_one_demo_variations",
        extra_kcs=["field"],
        output_dir="log_substitution_v2_author",
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=training_pool,
        n_problems=len(training_pool),
    )

    print(
        Fore.CYAN
        + f"Training on {len(training_pool)} problem(s) "
        + f"({1} base + {len(training_pool) - 1} random variations)..."
        + Style.RESET_ALL
    )
    trainer.start()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the substitution_v2 author agent on one demo and its variations."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for generating variation problems",
    )
    parser.add_argument(
        "--random-train-count",
        type=int,
        default=DEFAULT_RANDOM_TRAIN_COUNT,
        help=(
            "Number of random structural variations (same structure, new names/values) "
            "to include in training alongside the base demo"
        ),
    )
    parser.add_argument("--agent-type", default="DIPL")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)