"""Train substitution_v2 author agent and print curated action traces."""

from __future__ import annotations

import argparse
import faulthandler
import random
from pathlib import Path

import colorama
from colorama import Back, Fore, Style

from apprentice.agents.cre_agents.cre_agent import CREAgent

import tutorgym.helpers.ai2t_helpers  
from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.shared import Action
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
]


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


def build_training_sequence(env: SubstitutionTutorV2, n_problems: int) -> list[dict]:
    return [env.generate_random_problem() for _ in range(n_problems)]


def _state_to_kwargs(state, *, is_start: bool) -> dict:
    return {"state": state.objs, **state.annotations, "is_start": is_start}


def display_curated_problem_outputs(agent: CREAgent, env: SubstitutionTutorV2) -> None:
    print(Fore.CYAN + "\nShowing agent actions on curated substitution_v2 problems..." + Style.RESET_ALL)

    for index, problem in enumerate(CURATED_PROBLEMS, start=1):
        print(
            Back.WHITE
            + Fore.BLACK
            + f"\n=== Problem {index}: {problem['relationships'][-1]} ({problem['unknowns'][0]}) ==="
            + Style.RESET_ALL
        )

        env.set_problem(**problem)
        state = env.get_state()
        is_start = True
        step = 1

        while not state.get_annotation("is_done", False):
            agent_kwargs = _state_to_kwargs(state, is_start=is_start)
            action_payload = agent.act(**agent_kwargs, return_kind="action")
            if not action_payload:
                print(Fore.YELLOW + "Agent produced no action; stopping." + Style.RESET_ALL)
                break

            action = Action(action_payload)
            reward = env.check(action)
            print(
                Fore.BLUE
                + f"Step {step}:"
                + Style.RESET_ALL
                + f" {action.selection} -> {action.input}"
                + (f" [{reward:+d}]" if isinstance(reward, int) else "")
            )
            if action.annotations:
                extras = ", ".join(f"{k}={v}" for k, v in action.annotations.items())
                print(Fore.WHITE + f"  annotations: {extras}" + Style.RESET_ALL)

            if reward > 0:
                env.apply(action)
                state = env.get_state()
                is_start = False
                step += 1
            else:
                print(Fore.MAGENTA + "Halting because the environment rejected the action." + Style.RESET_ALL)
                break

        if state.get_annotation("is_done", False):
            print(Fore.GREEN + "Problem completed." + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "Problem left incomplete." + Style.RESET_ALL)


def run_training(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    env = SubstitutionTutorV2(
        problems=CURATED_PROBLEMS,
        demo_annotations=["arg_foci", "how_help"],
        check_annotations=["arg_foci"],
    )

    training_sequence = build_training_sequence(env, args.n_problems)
    log_dir = Path("log_substitution_v2_author_eval")
    logger = DataShopLogger(
        f"substitution_v2_eval_{args.agent_type}_{args.n_problems}probs",
        extra_kcs=["field"],
        output_dir=str(log_dir),
    )

    agent = make_agent()
    trainer = AuthorTrainer(
        agent,
        env,
        logger=logger,
        problem_set=training_sequence,
        n_problems=len(training_sequence),
    )

    print(Fore.CYAN + f"Running {len(training_sequence)} training problems..." + Style.RESET_ALL)
    trainer.start()

    display_curated_problem_outputs(agent, env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train DIPL on substitution v2 and print curated action traces")
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