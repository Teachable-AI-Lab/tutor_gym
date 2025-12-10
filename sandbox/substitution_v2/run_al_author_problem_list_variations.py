"""Train on each curated substitution_v2 problem plus inline variations."""
from __future__ import annotations

import argparse
import json
import random
import string
import re
from pathlib import Path
from typing import Dict, List, Tuple

import colorama
from colorama import Fore, Style

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers 
from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.shared import Action, ProblemState
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger

colorama.init(autoreset=True)

DEFAULT_PROBLEM_FILE = Path(__file__).with_name("problem_list.json")
DEFAULT_VARIATION_COUNT = 3
DEFAULT_RANDOM_SEED = 7


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
def load_problems(path: Path) -> List[Dict[str, object]]:

    with path.open() as problem_file:
        data = json.load(problem_file)

    if not isinstance(data, list):
        raise ValueError("Problem file must contain a JSON list of problems")

    problems: List[Dict[str, object]] = []
    for problem in data:
        if not isinstance(problem, dict):
            raise ValueError("Each entry in the problem list must be a JSON object")
        problems.append(problem)

    return problems


_IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_NUMBER_RE = re.compile(r"\d+")


def _remap_relationship(relationship: str, mapping: Dict[str, str], rng: random.Random) -> str:

    def repl_ident(match: re.Match[str]) -> str:
        ident = match.group(0)
        return mapping.get(ident, ident)

    remapped = _IDENTIFIER_RE.sub(repl_ident, relationship)

    return _randomize_numeric_string(remapped, rng, min_value=2, max_value=220)


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
            _remap_relationship(relationship, mapping, rng) for relationship in base_relationships
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


def _state_to_kwargs(state: ProblemState, is_start: bool) -> Dict:
    return {"state": state.objs, **state.annotations, "is_start": is_start}


def _format_action(
    prefix: str, action: Action, *, arg_foci: List[str] | None, how_help: str | None
) -> str:
    selection, _, value = action.as_tuple()
    return (
        f"{prefix}: {selection} -> {value} "
        f"arg_foci={arg_foci or []},how_help={how_help or ''}"
    )


def run_agent_on_problem(
    agent: CREAgent, problem: Dict[str, object], *, max_steps: int = 500
) -> Tuple[List[str], bool, str | None, List[str]]:

    tutor = SubstitutionTutorV2(problems=[problem])
    tutor.set_problem(**problem)
    target_len = len(tutor.substitution_targets)

    arg_foci_lookup = {
        widget_id: sources for widget_id, _, sources in tutor.substitution_targets
    }

    state = tutor.get_state()
    is_start = True
    final_tokens: List[str] = []
    actions_taken: List[str] = []
    failure_reason: str | None = None
    first_outcome: Dict[str, str] = {}
    early_incorrect = False

    for _ in range(max_steps):
        if state.get_annotation("is_done"):
            break

        kwargs = _state_to_kwargs(state, is_start)
        action_payload = agent.act(return_kind="action", **kwargs)

        if not action_payload:
            hint_action = None
            if getattr(tutor, "next_actions", None):
                hint_action = tutor.next_actions[0]

            if hint_action is None:
                failure_reason = "Agent did not return an action."
                break

            actions_taken.append(
                _format_action(
                    "HINT",
                    hint_action,
                    arg_foci=hint_action.annotations.get("arg_foci"),
                    how_help=hint_action.annotations.get("how_help"),
                )
            )
            sel, _, val = hint_action.as_tuple()
            if sel.startswith("substitution"):
                final_tokens.append(val)

            state = tutor.apply(hint_action)
            is_start = False
            continue

        action = Action(action_payload)
        selection, _, value = action.as_tuple()
        arg_foci = arg_foci_lookup.get(selection, [])
        how_help = None
        if selection.startswith("substitution"):
            how_help = "Copy from references"

        reward = tutor.check(action)
        if reward < 0:
            actions_taken.append(
                _format_action("INCORRECT", action, arg_foci=arg_foci, how_help=how_help)
            )
            if selection.startswith("substitution") and selection not in first_outcome:
                early_incorrect = True
                failure_reason = (
                    f"First attempt on {selection} was incorrect (value={value})."
                )
                first_outcome[selection] = "incorrect"
            continue

        actions_taken.append(
            _format_action("CORRECT", action, arg_foci=arg_foci, how_help=how_help)
        )

        if selection.startswith("substitution") and selection not in first_outcome:
            first_outcome[selection] = "correct"

        state = tutor.apply(action)
        actions_taken.append(f"APPLY: {selection} -> {value}")
        if selection.startswith("substitution"):
            final_tokens.append(value)

        is_start = False

    success = (
        not early_incorrect
        and (
            bool(state.get_annotation("is_done"))
            or len(final_tokens) == target_len
        )
    )

    return final_tokens, success, failure_reason, actions_taken


# ---------------------------------------------------------------------------
# Training and reporting
# ---------------------------------------------------------------------------
def build_training_pool(
    problems: List[Dict[str, object]], *, variation_count: int, seed: int
) -> List[Dict[str, object]]:
    rng = random.Random(seed)
    training_pool: List[Dict[str, object]] = []

    for idx, problem in enumerate(problems):
        training_pool.append(problem)
        if variation_count:
            variations = generate_variations(
                count=variation_count,
                base=problem,
                seed=rng.randint(0, 10_000) + idx,
            )
            training_pool.extend(variations)

    return training_pool


def run_training(args: argparse.Namespace) -> None:
    problem_path = Path(args.problem_list)
    base_problems = load_problems(problem_path)

    training_pool = build_training_pool(
        base_problems, variation_count=args.variation_count, seed=args.seed
    )

    env = SubstitutionTutorV2(
        problems=training_pool,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    logger = DataShopLogger(
        "substitution_v2_problem_list_variations",
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

    total_variations = len(training_pool) - len(base_problems)
    print(
        Fore.CYAN
        + f"Training on {len(training_pool)} problems "
        + f"({len(base_problems)} base + {total_variations} variations)..."
        + Style.RESET_ALL
    )
    trainer.start()

    print(
        Fore.CYAN
        + "\nReplaying training problems with training-style traces to count successes"
        + Style.RESET_ALL
    )

    completed = 0
    for index, problem in enumerate(training_pool, start=1):
        print(Fore.BLUE + f"\nProblem {index} definition:" + Style.RESET_ALL)
        print(json.dumps(problem, indent=2))

        tokens, success, failure_reason, actions = run_agent_on_problem(agent, problem)

        print(Fore.CYAN + f"Problem {index}: action trace" + Style.RESET_ALL)
        for step, action in enumerate(actions, start=1):
            print(f"  {step}. {action}")

        if success:
            completed += 1
            print(
                Fore.GREEN
                + f"Problem {index}: final answer tokens = {tokens}"\
                + Style.RESET_ALL
            )
        else:
            detail = f" ({failure_reason})" if failure_reason else ""
            print(
                Fore.YELLOW
                + f"Problem {index}: partial tokens = {tokens}{detail}"\
                + Style.RESET_ALL
            )

    print(
        Fore.MAGENTA
        + f"\nCompleted {completed} of {len(training_pool)} training problems."
        + Style.RESET_ALL
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train the substitution_v2 author agent on each curated problem plus "
            "inline structural variations, then replay the training set with "
            "training-style traces and success counts."
        )
    )
    parser.add_argument(
        "--problem-list",
        default=str(DEFAULT_PROBLEM_FILE),
        help="JSON file containing the curated substitution_v2 problems",
    )
    parser.add_argument(
        "--variation-count",
        type=int,
        default=DEFAULT_VARIATION_COUNT,
        help=(
            "Number of structural variations (same structure, new names/values) "
            "to generate for each base problem"
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for variation generation",
    )
    parser.add_argument("--agent-type", default="DIPL")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.agent_type.upper() != "DIPL":
        raise ValueError("Only DIPL is supported for this runner.")
    run_training(args)