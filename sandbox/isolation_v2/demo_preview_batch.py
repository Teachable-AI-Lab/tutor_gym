"""Batch preview utility for IsolationTutorV2 problems."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo_preview import ( 
    extract_widget_layout,
    gather_demo_steps,
    format_widget,
)
from tutorgym.env_classes.misc.isolation_v2.isolation_v2 import (  
    IsolationTutorV2,
)


def _infer_unknown(tokens: Iterable[str]) -> str:

    for token in tokens:
        if any(char.isalpha() for char in token):
            return token
    raise ValueError("Unable to infer unknown token from final token sequence")


def load_final_token_sets() -> List[Dict[str, Any]]:

    manifest_path = Path(__file__).with_name("final_tokens_unknowns_as_x.json")
    if not manifest_path.exists():
        raise FileNotFoundError(
            "Expected final_tokens.json next to demo_preview_batch.py; none found."
        )

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        problems = data.get("problems")
    else:
        problems = data

    if isinstance(problems, (str, bytes)) or not isinstance(
        problems, (list, tuple)
    ):
        raise ValueError(
            "final_tokens.json must contain an array of problem definitions"
        )

    normalised: List[Dict[str, Any]] = []
    for idx, entry in enumerate(problems, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry #{idx} is not an object: {entry!r}")
        if "final_tokens" not in entry:
            raise ValueError("Each entry must include a 'final_tokens' key")
        tokens = entry["final_tokens"]
        if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
            raise ValueError(
                f"Entry #{idx} has an invalid 'final_tokens' value: {tokens!r}"
            )

        unknown = entry.get("unknown") or _infer_unknown(tokens)
        normalised.append(
            {
                "equation_tokens": tokens,
                "unknown": unknown,
                "problem_index": entry.get("problem_index", idx),
                "source_entry": entry,
            }
        )

    if not normalised:
        raise ValueError("final_tokens.json did not define any problems")

    return normalised


def preview_problem(index: int, example: Dict[str, Any]) -> None:

    tutor = IsolationTutorV2(demo_annotations=["arg_foci", "how_help"])
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
    problems = load_final_token_sets()
    for idx, example in enumerate(problems, start=1):
        preview_problem(idx, example)


if __name__ == "__main__":
    main()