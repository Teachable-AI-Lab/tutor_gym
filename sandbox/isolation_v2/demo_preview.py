"""Utility script to visualise the Isolation V2 tutor's widgets and demo actions."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tutorgym.env_classes.misc.isolation_v2.isolation_v2 import IsolationTutorV2
from tutorgym.shared import Action, ProblemState

DEFAULT_EXAMPLE: Dict[str, Any] = {
    "equation_tokens": [
        "300",
        "+",
        "x",
        "=",
        "(",
        "2",
        "*",
        "x",
        ")",
        "+",
        "100",
    ],
    "unknown": "x",
}


def load_example() -> Dict[str, Any]:

    examples_path = Path(__file__).with_name("random_problem_examples.json")
    if examples_path.exists():
        data = json.loads(examples_path.read_text(encoding="utf-8"))
        examples = data.get("examples", [])
        if examples:
            return examples[0]
    return DEFAULT_EXAMPLE


def extract_widget_layout(state: ProblemState) -> List[Dict[str, Any]]:

    widgets: List[Dict[str, Any]] = []
    for widget_id, widget in state.items():
        entry = {
            "id": widget_id,
            "type": widget.get("type"),
            "locked": widget.get("locked"),
            "value": widget.get("value"),
            "x": widget.get("x"),
            "y": widget.get("y"),
            "width": widget.get("width"),
            "height": widget.get("height"),
        }
        widgets.append({k: v for k, v in entry.items() if v is not None})

    widgets.sort(key=lambda item: (item.get("y", 0), item.get("x", 0), item["id"]))
    return widgets


def collect_isolation_tokens(state: ProblemState) -> List[str]:

    tokens: List[tuple[int, str]] = []
    for widget_id, widget in state.items():
        if not widget_id.startswith("isolation_"):
            continue
        try:
            index = int(widget_id.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        value = widget.get("value")
        if value:
            tokens.append((index, value))

    return [value for _, value in sorted(tokens, key=lambda item: item[0])]


def gather_demo_steps(tutor: IsolationTutorV2) -> tuple[List[Action], List[str]]:

    steps: List[Action] = []
    final_tokens: List[str] = []

    while True:
        demos = tutor.get_all_demos()
        if not demos:
            break

        action = demos[0]
        steps.append(action)
        if tutor.action_is_done(action):
            break

        state = tutor.apply(action)
        final_tokens = collect_isolation_tokens(state)

    if not final_tokens:
        final_tokens = collect_isolation_tokens(tutor.state)

    return steps, final_tokens


def format_widget(widget: Dict[str, Any]) -> str:

    pieces: List[str] = [f"id={widget['id']}"]
    w_type = widget.get("type")
    if w_type:
        pieces.append(f"type={w_type}")
    if "locked" in widget:
        pieces.append(f"locked={widget['locked']}")
    if "value" in widget:
        pieces.append(f"value={widget['value']!r}")
    if "x" in widget and "y" in widget:
        pieces.append(f"pos=({widget['x']}, {widget['y']})")
    if "width" in widget and "height" in widget:
        pieces.append(f"size={widget['width']}x{widget['height']}")
    return ", ".join(pieces)


def main() -> None:
    example = load_example()

    tutor = IsolationTutorV2(demo_annotations=["arg_foci", "how_help"])
    tutor.set_problem(**example)

    print("Input example:")
    print(f"  equation_tokens: {example['equation_tokens']}")
    print(f"  unknown: {example['unknown']}")

    print("\nWidget formation:")
    widget_layout = extract_widget_layout(tutor.start_state)
    for widget in widget_layout:
        print(f"  - {format_widget(widget)}")

    print("\nDemo actions:")
    demo_steps, final_tokens = gather_demo_steps(tutor)
    for idx, action in enumerate(demo_steps, start=1):
        arg_foci = action.annotations.get("arg_foci", [])
        print(
            f"Step {idx}: selection={action.selection}, input={action.input!r}, "
            f"arg_foci={arg_foci}"
        )

    print("\nFinal answer tokens:")
    print(f"  {final_tokens}")


if __name__ == "__main__":
    main()