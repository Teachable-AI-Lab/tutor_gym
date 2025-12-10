"""Utility script to display substitution_v2 widget layout and demo actions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.shared import Action


EXAMPLE_PROBLEM: Dict[str, object] = {"variables": ["m","j","r1","r2","t","s"],
"quantities": {"j": "2500", "r1": "2", "r2": "5", "s": "200"},
"relationships": ["m / j = r1 / r2", "t = m - s"],
"unknowns": ["t"]}

def _format_widget_row(row: List[Tuple[str, Dict]]) -> str:
    pieces = []
    for widget_id, data in row:
        locked = "locked" if data.get("locked") else "open"
        value = data.get("value", "")
        pieces.append(f"{widget_id}: {value!r} ({locked})")
    return " | ".join(pieces)


def print_widget_layout(tutor: SubstitutionTutorV2) -> None:
    state = tutor.start_state
    rows: Dict[int, List[Tuple[str, Dict]]] = {}
    for widget_id, data in state.items():
        y = data.get("y", 0)
        rows.setdefault(y, []).append((widget_id, data))

    print("Widget formation:")
    for y in sorted(rows):
        row_widgets = sorted(rows[y], key=lambda item: item[1].get("x", 0))
        print(f"  y={y}: {_format_widget_row(row_widgets)}")
    print()


def print_demo_actions(tutor: SubstitutionTutorV2) -> None:
    print("Demo actions:")
    for step, (widget_id, token_value, sources) in enumerate(tutor.substitution_targets, start=1):
        action = Action((widget_id, "UpdateTextField", token_value), arg_foci=sources)
        annotations = action.annotations
        arg_foci = annotations.get("arg_foci", [])
        print(
            f"  Step {step}: selection={widget_id}, input={token_value!r}, "
            f"arg_foci={arg_foci}"
        )
    print(f"  Step {len(tutor.substitution_targets) + 1}: selection=done, action=PressButton")
    final_tokens = [token_value for _, token_value, _ in tutor.substitution_targets]
    print(f"Final answer tokens: {final_tokens}")
    print()

def _load_problem(arg: str | None) -> Dict[str, object]:
    if arg is None:
        return EXAMPLE_PROBLEM

    if arg == "-":
        raw = sys.stdin.read()
    else:
        path = Path(arg)
        if path.is_file():
            raw = path.read_text()
        else:
            raw = arg

    try:
        problem = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse problem JSON: {exc}") from exc

    if not isinstance(problem, dict):
        raise SystemExit("Problem JSON must decode to an object/dict.")

    return problem


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Display the widgets and demonstration actions produced by "
            "SubstitutionTutorV2 for the supplied problem."
        )
    )
    parser.add_argument(
        "problem",
        nargs="?",
        help=(
            "Path to a JSON file, an inline JSON string, or '-' to read from "
            "stdin. Defaults to the canonical substitution_v2 example."
        ),
    )
    args = parser.parse_args(argv)

    problem = _load_problem(args.problem)

    tutor = SubstitutionTutorV2(problems=[problem])
    tutor.set_problem(**problem)

    print("Problem input:")
    print(json.dumps(problem, indent=2))
    print()

    print_widget_layout(tutor)
    print_demo_actions(tutor)


if __name__ == "__main__":
    main()