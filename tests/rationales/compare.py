#!/usr/bin/env python3
"""Compare extracted rationales against a golden YAML expectation.

Outputs JSON with precision, recall, matched/unmatched lists, and exit code
0 if thresholds met, 1 otherwise.

Usage:
    python3 compare.py <expected.yaml> <actual.yaml> [--precision-min=0.85] [--recall-min=0.70] [--expected-count=N]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)


CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}


def load_yaml(path: str) -> list[dict]:
    content = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(content) or []
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a list at top level, got {type(data).__name__}")
    return data


def matches(expected: dict, actual: dict) -> bool:
    text = (actual.get("text") or "").lower()
    for needle in expected.get("text_contains", []):
        if needle.lower() not in text:
            return False

    if expected.get("kind") and actual.get("kind") != expected["kind"]:
        return False

    min_conf = expected.get("min_confidence")
    if min_conf:
        actual_conf = actual.get("confidence", "low")
        if CONFIDENCE_RANK.get(actual_conf, 0) < CONFIDENCE_RANK.get(min_conf, 0):
            return False

    source_needles = expected.get("source_contains", [])
    if source_needles:
        source = (actual.get("source") or "").lower()
        for needle in source_needles:
            if needle.lower() not in source:
                return False

    return True


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2:
        sys.stderr.write(__doc__)
        return 2

    expected_path, actual_path = args[0], args[1]
    precision_min = 0.85
    recall_min = 0.70
    expected_count_override = None

    for arg in args[2:]:
        if arg.startswith("--precision-min="):
            precision_min = float(arg.split("=", 1)[1])
        elif arg.startswith("--recall-min="):
            recall_min = float(arg.split("=", 1)[1])
        elif arg.startswith("--expected-count="):
            expected_count_override = int(arg.split("=", 1)[1])

    expected = load_yaml(expected_path)
    actual = load_yaml(actual_path)

    # Control-page mode: expected_count == 0 means any extraction is failure
    if expected_count_override == 0:
        result = {
            "mode": "control",
            "expected_count": 0,
            "actual_count": len(actual),
            "false_positives": actual,
            "passed": len(actual) == 0,
        }
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1

    matched_pairs: list[tuple[int, int]] = []
    matched_expected: set[int] = set()
    matched_actual: set[int] = set()

    for ei, exp in enumerate(expected):
        for ai, act in enumerate(actual):
            if ai in matched_actual:
                continue
            if matches(exp, act):
                matched_pairs.append((ei, ai))
                matched_expected.add(ei)
                matched_actual.add(ai)
                break

    tp = len(matched_pairs)
    fp = len(actual) - tp
    fn = len(expected) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    unmatched_expected = [expected[i] for i in range(len(expected)) if i not in matched_expected]
    unmatched_actual = [actual[i] for i in range(len(actual)) if i not in matched_actual]

    result = {
        "mode": "golden",
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "precision_min": precision_min,
        "recall_min": recall_min,
        "matched_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "unmatched_expected": unmatched_expected,
        "unmatched_actual_keys": [
            {"text_first_80": (a.get("text") or "")[:80], "kind": a.get("kind")}
            for a in unmatched_actual
        ],
        "passed": precision >= precision_min and recall >= recall_min,
    }

    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
