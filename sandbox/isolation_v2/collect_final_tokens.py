"""Generate final token sequences for IsolationTutorV2 problems."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo_preview import ( 
    gather_demo_steps,
)
from demo_preview_batch import ( 
    load_final_token_sets,
)
from tutorgym.env_classes.misc.isolation_v2.isolation_v2 import (
    IsolationTutorV2,
)

DEFAULT_OUTPUT = Path(__file__).with_name("computed_final_tokens.json")


def collect_final_tokens() -> List[Dict[str, Any]]:

    problems = load_final_token_sets()
    results: List[Dict[str, Any]] = []

    for idx, example in enumerate(problems, start=1):
        tutor = IsolationTutorV2(demo_annotations=["arg_foci", "how_help"])
        tutor.set_problem(
            equation_tokens=example["equation_tokens"], unknown=example["unknown"]
        )

        _, final_tokens = gather_demo_steps(tutor)
        results.append(
            {
                "problem_index": example.get("problem_index", idx),
                "unknown": example["unknown"],
                "final_tokens": final_tokens,
            }
        )

    return results


def write_results(results: List[Dict[str, Any]], output_path: Path = DEFAULT_OUTPUT) -> None:

    payload = json.dumps(results, indent=2, ensure_ascii=False)
    output_path.write_text(payload + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} entries to {output_path}")


def main(output_path: Path = DEFAULT_OUTPUT) -> None:
    results = collect_final_tokens()
    write_results(results, output_path)


if __name__ == "__main__":
    main()