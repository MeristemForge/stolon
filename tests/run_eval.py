#!/usr/bin/env python3
"""Universal skill eval runner for stolon.

Usage:
    python run_eval.py                          # run all skills
    python run_eval.py c-development            # run one skill
    python run_eval.py c-development path/to/outputs  # custom output dir
"""

import importlib.util
import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
EVALS_DIR = TESTS_DIR / "evals"


def load_checks_module(skill_dir: Path):
    """Dynamically load a skill's checks.py as a module."""
    checks_path = skill_dir / "checks.py"
    if not checks_path.exists():
        raise FileNotFoundError(f"{checks_path} not found")
    spec = importlib.util.spec_from_file_location("checks", checks_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_skill_eval(skill_name: str, output_dir: Path) -> tuple[int, int, int]:
    skill_dir = EVALS_DIR / skill_name
    prompts_path = skill_dir / "prompts.json"

    if not prompts_path.exists():
        print(f"  ERROR: {prompts_path} not found")
        return 0, 1, 0

    checks_mod = load_checks_module(skill_dir)
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))

    passed = failed = skipped = 0

    for prompt in prompts:
        eval_id = prompt["id"]
        expected = prompt["expected_checks"]
        print(f"\n  --- {eval_id} ---")

        prompt_dir = output_dir / eval_id
        if not prompt_dir.is_dir():
            print(f"    - no output directory (skipped)")
            skipped += 1
            continue

        output_file = prompt_dir / "output.txt"
        project_dir = prompt_dir / "project"

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

            # Determine input type from function's 'input_type' attribute
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

    return passed, failed, skipped


def main():
    skill_filter = sys.argv[1] if len(sys.argv) > 1 else None
    custom_output = sys.argv[2] if len(sys.argv) > 2 else None

    if skill_filter:
        skills = [skill_filter]
    else:
        skills = sorted(
            d.name for d in EVALS_DIR.iterdir()
            if d.is_dir() and d.name != "integration"
        )

    total_pass = total_fail = total_skip = 0

    for skill in skills:
        print(f"\n=== Skill: {skill} ===")

        if custom_output:
            out_dir = Path(custom_output)
        else:
            out_dir = EVALS_DIR / skill / "baselines"

        p, f, s = run_skill_eval(skill, out_dir)
        total_pass += p
        total_fail += f
        total_skip += s

    print(f"\n===============================")
    print(f"  PASSED:  {total_pass}")
    print(f"  FAILED:  {total_fail}")
    print(f"  SKIPPED: {total_skip}")
    print(f"===============================")

    sys.exit(1 if total_fail > 0 else 0)


if __name__ == "__main__":
    main()

