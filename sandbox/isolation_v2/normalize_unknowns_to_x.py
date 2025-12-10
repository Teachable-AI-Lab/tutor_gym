from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Dict, Any

UNKNOWN_PATTERN = re.compile(r"[A-Za-z]")

def _load_final_tokens(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _normalize_tokens(tokens: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    for tok in tokens:
        normalized.append("x" if UNKNOWN_PATTERN.search(tok) else tok)
    return normalized

def _normalize_problems(problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_problems: List[Dict[str, Any]] = []
    for problem in problems:
        new_problem = {"problem_index": problem.get("problem_index")}
        tokens = problem.get("final_tokens", [])
        new_problem["final_tokens"] = _normalize_tokens(tokens)
        normalized_problems.append(new_problem)
    return normalized_problems

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    source_path = base_dir / "final_tokens(test).json"
    dest_path = base_dir / "final_tokens_unknowns_as_x(test).json"

    problems = _load_final_tokens(source_path)
    normalized = _normalize_problems(problems)

    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)

    print(f"Wrote {len(normalized)} problems with normalized unknowns to {dest_path}")

if __name__ == "__main__":
    main()