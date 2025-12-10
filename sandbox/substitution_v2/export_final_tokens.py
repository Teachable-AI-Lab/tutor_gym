"""Export final substitution_v2 answer tokens for a batch of problems."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tutorgym.env_classes.misc.substitution_v2 import SubstitutionTutorV2


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
        raise SystemExit("Problem list is empty; nothing to export.")

    return problems


def _collect_final_tokens(problem: Dict[str, object]) -> List[str]:
    tutor = SubstitutionTutorV2(problems=[problem])
    tutor.set_problem(**problem)
    return [token_value for _, token_value, _ in tutor.substitution_targets]


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute the final substitution_v2 answer tokens for each problem in a "
            "JSON array and save them to disk."
        )
    )

    default_problem_file = Path(__file__).with_name("problem_list.json")
    default_output_file = Path(__file__).with_name("final_tokens.json")

    parser.add_argument(
        "problem_file",
        nargs="?",
        default=str(default_problem_file),
        help=(
            "Path to a JSON file containing a list of substitution_v2 problem "
            "objects. Defaults to problem_list.json next to this script."
        ),
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default=str(default_output_file),
        help=(
            "Path to write the JSON array of final answer tokens. Defaults to "
            "final_tokens.json next to this script."
        ),
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    problems = _load_problem_file(args.problem_file)

    results = []
    for index, problem in enumerate(problems, start=1):
        final_tokens = _collect_final_tokens(problem)
        results.append(
            {
                "problem_index": index,
                "final_tokens": final_tokens,
            }
        )

    output_path = Path(args.output_file)
    output_path.write_text(json.dumps(results, indent=2))
    print(f"Saved final tokens for {len(results)} problems to {output_path}")


if __name__ == "__main__":
    main()