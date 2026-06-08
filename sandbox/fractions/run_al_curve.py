"""
Run N independent AL agents through the fraction tutoring system and plot
an aggregated learning curve (mean +/- SE of per-problem error rate).

Usage:
    python sandbox/fractions/run_al_curve.py --condition bkt --num_agents 10
    python sandbox/fractions/run_al_curve.py --condition blocked --num_agents 5 --output my_curve.png
"""

import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from colorama import Back, Fore, Style
from random import shuffle

from tutorgym.trainer import Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.eval.llm_stu_eval import (
    FRAC_AS_PROBLEMS, FRAC_AD_PROBLEMS, FRAC_M_PROBLEMS, FRAC_ALL_PROBLEMS,
    fraction_bkt_probs,
    SimpleBlockedController, SimpleInterleaveController, BKTTrackingInterleaveController,
)

_FRAC_KCS = ["fraction_add_same", "fraction_add_different", "fraction_multiply"]

_FRAC_CRE_AGENT_ARGS = {
    "function_set": ["Add", "Multiply", "Copy", "AcrossMultiply"],
    "feature_set": ["Equals"],
    "planner": "set_chaining",
    "explanation_choice": "least_operations",
    "search_depth": 2,
    "where_learner": "mostspecific",
    "when_learner": "decision_tree",
    "which_learner": "when_prediction",
    "action_chooser": "max_which_utility",
    "suggest_uncert_neg": True,
    "error_on_bottom_out": False,
    "extra_features": ["Match"],
    "when_args": {"encode_relative": True, "one_hot": True},
    "should_find_neighbors": True,
}

def _make_cre_agent():
    from apprentice.agents.cre_agents.cre_agent import CREAgent
    import tutorgym.helpers.ai2t_helpers
    return CREAgent(**_FRAC_CRE_AGENT_ARGS)


class TrackingTrainer(Trainer):
    """Trainer subclass that records per-problem error rate (incorrect+hint / total steps)."""

    def start(self):
        self.problem_error_rates = []
        self.logger.set_student()
        p = 1
        p_iter = self.problem_iterator
        for prob_args in p_iter:
            if prob_args is None:
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(**prob_args)
            self.logger.set_problem(self.env.problem_name)

            c0 = self.total_correct
            i0 = self.total_incorrect

            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {self.env.problem_name}" + Style.RESET_ALL)

            is_start = True
            incorr_streak = 0
            while True:
                state = self.env.get_state()
                if state.get_annotation("is_done") == True:
                    break
                force_demo = (self.num_incorrect_force_demo >= 0 and
                              incorr_streak >= self.num_incorrect_force_demo)
                rew = self.tutor_train_state(state, is_start=is_start, force_demo=force_demo)
                if rew > 0:
                    incorr_streak = 0
                    is_start = False
                else:
                    incorr_streak += 1

            dc = self.total_correct - c0
            di = self.total_incorrect - i0
            # Hints excluded (match R code: only INCORRECT=1, CORRECT=0, HINT filtered out)
            attempt_total = dc + di
            error_rate = di / attempt_total if attempt_total > 0 else 0.0
            self.problem_error_rates.append(error_rate)

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}"
                  f"  |  error_rate={error_rate:.3f}")
            p += 1

        total = self.total_hints + self.total_incorrect + self.total_correct
        if total > 0:
            print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect},'
                  f' hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
            print(f'PERCENTS(correct:{100*self.total_correct/total:.2f}%,'
                  f' incorrect:{100*self.total_incorrect/total:.2f}%,'
                  f' hint:{100*self.total_hints/total:.2f}%,'
                  f' assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')


def run_one_agent(condition, max_cycles, agent_idx):
    """Run a single fresh agent and return its per-problem error rates."""
    logger = DataShopLogger(
        f"AL_Fractions_{condition.capitalize()}_Curve_Agent{agent_idx}",
        output_dir=f'stu_eval_logs/al_fractions_{condition}_curve',
        extra_kcs=_FRAC_KCS,
    )
    env = FractionArithmetic()
    agent = _make_cre_agent()

    if condition == "bkt":
        controller = BKTTrackingInterleaveController(
            FRAC_ALL_PROBLEMS,
            bkt_probs=fraction_bkt_probs,
            max_cycles=max_cycles,
            mastery_threshold=0.95,
        )
    elif condition == "blocked":
        as_block = FRAC_AS_PROBLEMS.copy()
        ad_block = FRAC_AD_PROBLEMS.copy()
        m_block  = FRAC_M_PROBLEMS.copy()
        shuffle(as_block); shuffle(ad_block); shuffle(m_block)
        controller = SimpleBlockedController(as_block + ad_block + m_block, max_cycles=max_cycles)
    elif condition == "interleaved":
        all_probs = FRAC_ALL_PROBLEMS.copy()
        shuffle(all_probs)
        controller = SimpleInterleaveController(all_probs, max_cycles=max_cycles)
    else:
        raise ValueError(f"Unknown condition: {condition}")

    trainer = TrackingTrainer(
        agent, env,
        logger=logger,
        outer_loop_controller=controller,
        num_incorrect_force_demo=2,
    )
    trainer.start()
    print(f"-- AL FRACTIONS {condition.upper()} AGENT {agent_idx} END --")
    return trainer.problem_error_rates


_CONDITION_COLORS = {
    "blocked":    "red",
    "interleaved": "#5B9BD5",
    "bkt":        "darkgreen",
}

def plot_learning_curve(all_curves, condition, output_path):
    n = len(all_curves)
    max_len = max(len(c) for c in all_curves)

    # Pad with 0.0: agents that finish early have mastered all KCs,
    # so their error on any subsequent problem would be 0.
    padded = np.zeros((n, max_len))
    for i, c in enumerate(all_curves):
        padded[i, :len(c)] = c

    means = np.mean(padded, axis=0)
    stds = np.std(padded, axis=0, ddof=1)
    sems = stds / np.sqrt(n)

    xs = np.arange(1, max_len + 1)
    color = _CONDITION_COLORS.get(condition, "steelblue")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(xs, means, color=color, linewidth=0.7)
    ax.scatter(xs, means, color=color, s=18, zorder=3)
    ax.errorbar(xs, means, yerr=sems, fmt='none', ecolor=color,
                capsize=3, elinewidth=0.4, alpha=0.7)

    ax.set_xlabel("Problem Number", fontsize=13)
    ax.set_ylabel("Average Problem Error", fontsize=13)
    ax.set_title(condition.capitalize(), fontsize=14, fontweight='bold', ha='center')
    ax.set_xlim(0, max(20, max_len + 1))
    ax.set_ylim(0, 1)
    ax.set_xticks(range(0, max(21, max_len + 2), 10))
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.grid(axis='both', color='#D9D9D9', linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot to {output_path}")


if __name__ == "__main__":
    import faulthandler; faulthandler.enable()

    parser = argparse.ArgumentParser(
        description='Run N independent AL agents and plot an aggregated learning curve')
    parser.add_argument('--condition', type=str, default="bkt",
                        choices=['blocked', 'interleaved', 'bkt'],
                        help='Which condition to run')
    parser.add_argument('--num_agents', type=int, default=10,
                        help='Number of independent agents to run (default: 10)')
    parser.add_argument('--max_cycles', type=int, default=None,
                        help='Max cycles (defaults: 48 for bkt, 1 for blocked/interleaved)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output PNG path (default: learning_curve_<condition>.png)')
    args = parser.parse_args()

    if args.max_cycles is None:
        args.max_cycles = 48 if args.condition == "bkt" else 1
    if args.output is None:
        args.output = f"learning_curve_{args.condition}.png"

    print(f"Running fractions/{args.condition} with {args.num_agents} independent agent(s)")

    all_curves = []
    for i in range(args.num_agents):
        print(f"\n{'='*60}")
        print(f"  Agent {i+1}/{args.num_agents}")
        print(f"{'='*60}")
        curve = run_one_agent(args.condition, args.max_cycles, i + 1)
        all_curves.append(curve)
        print(f"Agent {i+1}: {len(curve)} problems, mean error={np.mean(curve):.3f}")

    plot_learning_curve(all_curves, args.condition, args.output)
    print(f"\nDone. {args.num_agents} agents, plot saved to {args.output}")
