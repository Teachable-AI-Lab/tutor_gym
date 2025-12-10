"""Display substitution_v2 widgets and demos for a list of problems."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2
from tutorgym.shared import Action


def _format_widget_row(row: List[Tuple[str, Dict]]) -> str:
    pieces = []
    for widget_id, data in row:
        locked = "locked" if data.get("locked") else "open"
        value = data.get("value", "")
        pieces.append(f"{widget_id}: {value!r} ({locked})")
    return " | ".join(pieces)


def _print_widget_layout(tutor: SubstitutionTutorV2) -> None:
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


def _print_demo_actions(tutor: SubstitutionTutorV2) -> None:
    print("Demo actions:")
    for step, (widget_id, token_value, sources) in enumerate(
        tutor.substitution_targets, start=1
    ):
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


def _load_problem_file(path: str) -> List[Dict[str, object]]:
    source = Path(path)
    if not source.is_file():
        raise SystemExit(f"Problem list file not found: {path}")

    try:
        payload = json.loads(source.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse problem list JSON: {exc}") from exc

    if not isinstance(payload, list):
        raise SystemExit("Problem list must be a JSON array of problem objects.")

    problems: List[Dict[str, object]] = []
    for index, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            raise SystemExit(
                f"Problem at index {index} is not a JSON object: {entry!r}"
            )
        problems.append(entry)
    if not problems:
        raise SystemExit("Problem list is empty; nothing to display.")
    return problems


def _display_problem(problem: Dict[str, object], label: str) -> None:
    tutor = SubstitutionTutorV2(problems=[problem])
    tutor.set_problem(**problem)

    print(f"=== {label} ===")
    print("Problem input:")
    print(json.dumps(problem, indent=2))
    print()

    _print_widget_layout(tutor)
    _print_demo_actions(tutor)



def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Display the widgets and demo actions produced by SubstitutionTutorV2 "
            "for each problem in the provided JSON array."
        )
    )
    default_problem_file = Path(__file__).with_name("test_problems.json")

    parser.add_argument(
        "problem_file",
        nargs="?",
        default=str(default_problem_file),
        help=(
            "Path to a JSON file containing a list of problem objects in the "
            "standard substitution_v2 schema. Defaults to the bundled "
            "problem_list.json next to this script."
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    problems = _load_problem_file(args.problem_file)

    if args.problem_file == str(default_problem_file):
        print(f"Loaded default problem list: {default_problem_file}")
        print()

    for idx, problem in enumerate(problems, start=1):
        label = f"Problem {idx}"
        _display_problem(problem, label)
        if idx != len(problems):
            print()


if __name__ == "__main__":
    main()