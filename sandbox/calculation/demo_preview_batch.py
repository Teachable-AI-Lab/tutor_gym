"""Batch preview utility for CalculationTutor problems."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tutorgym.env_classes.misc.calculation.calculation import CalculationTutor  
from demo_preview import (  
    extract_widget_layout,
    gather_demo_steps,
    format_widget,
)

COMPUTED_TOKENS_PATH = Path(__file__).with_name("computed_final_tokens.json")


def load_computed_token_sets(path: Path | None = None) -> List[Dict[str, Any]]:

    if path is None:
        path = COMPUTED_TOKENS_PATH

    if not path.exists():
        raise FileNotFoundError(
            "Expected computed_final_tokens.json next to demo_preview_batch.py"
        )

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        problems = data.get("problems")
    else:
        problems = data

    if isinstance(problems, (str, bytes)) or not isinstance(problems, (list, tuple)):
        raise ValueError(
            "computed_final_tokens.json must contain an array of problem definitions"
        )

    normalised: List[Dict[str, Any]] = []
    for idx, entry in enumerate(problems, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry #{idx} is not an object: {entry!r}")
        tokens = entry.get("final_tokens")
        if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
            raise ValueError(
                f"Entry #{idx} has an invalid 'final_tokens' value: {tokens!r}"
            )
        unknown = entry.get("unknown")
        if not unknown or not isinstance(unknown, str):
            raise ValueError(f"Entry #{idx} is missing an 'unknown' token")

        normalised.append(
            {
                "equation_tokens": tokens,
                "unknown": unknown,
                "problem_index": entry.get("problem_index", idx),
                "source_entry": entry,
            }
        )

    if not normalised:
        raise ValueError("computed_final_tokens.json did not define any problems")

    return normalised


def preview_problem(index: int, example: Dict[str, Any]) -> None:

    tutor = CalculationTutor(demo_annotations=["arg_foci", "how_help"])
    tutor.set_problem(
        equation_tokens=example["equation_tokens"], unknown=example["unknown"]
    )

    display_index = example.get("problem_index", index)
    print(f"Problem {index} (problem_index={display_index}):")
    print(f"  equation_tokens: {example['equation_tokens']}")
    print(f"  unknown: {example['unknown']}")

    print("\n  Widget formation:")
    widget_layout = extract_widget_layout(tutor.start_state)
    for widget in widget_layout:
        print(f"    - {format_widget(widget)}")

    print("\n  Demo actions:")
    demo_steps, final_tokens = gather_demo_steps(tutor)
    for step_index, action in enumerate(demo_steps, start=1):
        arg_foci = action.annotations.get("arg_foci", [])
        print(
            "    "
            f"Step {step_index}: selection={action.selection}, "
            f"input={action.input!r}, arg_foci={arg_foci}"
        )

    print("\n  Final answer tokens:")
    print(f"    {final_tokens}\n")


def main() -> None:
    problems = load_computed_token_sets()
    for idx, example in enumerate(problems, start=1):
        preview_problem(idx, example)


if __name__ == "__main__":
    main()