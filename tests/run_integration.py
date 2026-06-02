#!/usr/bin/env python3
"""Integration test runner for cross-skill validation.

Integration tests pull baselines from other skill evals and run
cross-skill checks against them. This validates handoff points
between skills in the chain: init -> style -> build -> debug -> commit.

Usage:
    python run_integration.py
"""

import importlib.util
import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
EVALS_DIR = TESTS_DIR / "evals"
INTEGRATION_DIR = EVALS_DIR / "integration"


def load_checks_module(checks_path: Path):
    spec = importlib.util.spec_from_file_location("checks", checks_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    checks_mod = load_checks_module(INTEGRATION_DIR / "checks.py")
    prompts = json.loads(
        (INTEGRATION_DIR / "prompts.json").read_text(encoding="utf-8")
    )

    passed = failed = skipped = 0

    print("\n=== Cross-Skill Integration Tests ===\n")

    for prompt in prompts:
        eval_id = prompt["id"]
        source_skill = prompt.get("source_skill")
        source_baseline = prompt.get("source_baseline")
        expected = prompt["expected_checks"]

        print(f"  --- {eval_id} ({source_skill}/{source_baseline}) ---")

        if not source_skill or not source_baseline:
            print(f"    - missing source_skill or source_baseline (skipped)")
            skipped += len(expected)
            continue

        baseline_dir = EVALS_DIR / source_skill / "baselines" / source_baseline

        if not baseline_dir.is_dir():
            print(f"    - baseline dir not found: {baseline_dir} (skipped)")
            skipped += len(expected)
            continue

        output_file = baseline_dir / "output.txt"
        project_dir = baseline_dir / "project"

        output_text = ""
        if output_file.exists():
            output_text = output_file.read_text(encoding="utf-8")

        for check_name in expected:
            fn_name = f"check_{check_name}"
            fn = getattr(checks_mod, fn_name, None)

            if fn is None:
                print(f"    - {check_name} (undefined)")
                skipped += 1
                continue

            input_type = getattr(fn, "input_type", "text")

            try:
                if input_type == "directory":
                    if project_dir.is_dir():
                        result = fn(project_dir)
                    else:
                        print(f"    - {check_name} (no project dir)")
                        skipped += 1
                        continue
                else:
                    if output_text:
                        result = fn(output_text)
                    else:
                        print(f"    - {check_name} (no output)")
                        skipped += 1
                        continue

                if result:
                    print(f"    [PASS] {check_name}")
                    passed += 1
                else:
                    print(f"    [FAIL] {check_name}")
                    failed += 1
            except Exception as e:
                print(f"    [FAIL] {check_name} (error: {e})")
                failed += 1

    print(f"\n===============================")
    print(f"  PASSED:  {passed}")
    print(f"  FAILED:  {failed}")
    print(f"  SKIPPED: {skipped}")
    print(f"===============================")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
