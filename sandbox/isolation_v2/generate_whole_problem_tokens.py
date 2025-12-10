"""Generate whole_problem_tokens.json with variations for isolation_v2.

This utility reads the existing ``final_tokens.json`` manifest, appends each
original problem, and then adds a fixed number of structure-preserving numeric
variations for that problem. The output preserves ordering: each original
problem immediately precedes its variants.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DEFAULT_SEED = 1729
DEFAULT_VARIATIONS_PER_PROBLEM = 0
INT_MIN, INT_MAX = 1, 200


def _load_final_tokens() -> List[Dict[str, object]]:
    manifest_path = Path(__file__).with_name("final_tokens_unknowns_as_x.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("problems", [])


def _infer_unknown(tokens: Iterable[str]) -> str:
    for token in tokens:
        if any(char.isalpha() for char in token):
            return token
    raise ValueError("Unable to infer unknown token from tokens: %r" % (tokens,))


def _is_numeric_token(token: str) -> bool:

    if any(char.isalpha() for char in token):
        return False
    allowed_chars = set("0123456789./")
    if not token or any(ch not in allowed_chars for ch in token):
        return False
    if token in {"/", "."}:
        return False
    if token.count("/") > 1 or token.count(".") > 1:
        return False
    if token[0] in {"/", "."} or token[-1] in {"/", "."}:
        return False
    return True


def _mutate_token(token: str, rng: random.Random) -> str:
    if not _is_numeric_token(token):
        return token

    if "/" in token:
        numerator_digits = len(token.split("/")[0])
        denominator_digits = len(token.split("/")[1])
        numerator = rng.randint(INT_MIN, INT_MAX)
        denominator = rng.randint(INT_MIN, INT_MAX)
        numerator_fmt = f"{numerator:0{numerator_digits}d}" if numerator_digits > 1 else str(numerator)
        denominator_fmt = (
            f"{denominator:0{denominator_digits}d}" if denominator_digits > 1 else str(denominator)
        )
        return f"{numerator_fmt}/{denominator_fmt}"

    if "." in token:
        decimals = len(token.split(".")[1])
        value = round(rng.uniform(float(INT_MIN), float(INT_MAX)), decimals)
        return f"{value:.{decimals}f}"

    return str(rng.randint(INT_MIN, INT_MAX))


def _make_variation(tokens: Iterable[str], rng: random.Random) -> List[str]:
    return [_mutate_token(token, rng) for token in tokens]


def build_whole_problem_manifest(
    *, seed: int = DEFAULT_SEED, variations_per_problem: int = DEFAULT_VARIATIONS_PER_PROBLEM
) -> List[Dict[str, object]]:
    rng = random.Random(seed)
    source = _load_final_tokens()

    manifest: List[Dict[str, object]] = []
    for idx, entry in enumerate(source, start=1):
        tokens = entry["final_tokens"]
        unknown = entry.get("unknown") or _infer_unknown(tokens)
        problem_index = entry.get("problem_index", idx)

        manifest.append(
            {
                "problem_index": problem_index,
                "unknown": unknown,
                "equation_tokens": tokens,
                "variant_index": 0,
            }
        )

        for variant_offset in range(1, variations_per_problem + 1):
            variant_tokens = _make_variation(tokens, rng)
            manifest.append(
                {
                    "problem_index": problem_index,
                    "unknown": unknown,
                    "equation_tokens": variant_tokens,
                    "variant_index": variant_offset,
                }
            )

    return manifest


def write_whole_problem_manifest(path: Path | None = None) -> Path:
    path = path or Path(__file__).with_name("whole_problem_tokens.json")
    manifest = build_whole_problem_manifest()
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    output_path = write_whole_problem_manifest()
    print(f"Wrote {output_path}")