#!/usr/bin/env python3
"""Universal skill eval runner for stolon.

Two modes:

  Baseline mode (default) -- runs checks against the committed sample answers
  in baselines/<id>/output.txt. Fast and deterministic, but it tests a frozen
  snapshot, not the live agent. A green run means "the committed sample still
  contains the right shape", not "the agent obeys the skill".

  Live mode (--live) -- actually invokes a real agent per prompt and runs the
  checks against ITS output. This is the only mode that measures the agent
  rather than a snapshot. It requires an agent command in the environment
  variable STOLON_AGENT_CMD; the composed prompt (skill reference + user
  prompt) is written to the command's stdin and the response is read from
  stdout. With no STOLON_AGENT_CMD set, --live falls back to baseline mode
  and says so.

Usage:
    python run_eval.py                          # all skills, baseline mode
    python run_eval.py c-project-style          # one skill, baseline mode
    python run_eval.py c-project-style path/to/outputs   # custom output dir
    python run_eval.py --live                   # all skills, live agent
    python run_eval.py --live c-project-style   # one skill, live agent

Environment (live mode):
    STOLON_AGENT_CMD   shell command that reads a prompt on stdin and writes
                       the agent response to stdout (e.g. "myagent --quiet").
    STOLON_AGENT_TIMEOUT  per-prompt timeout in seconds (default 180).
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
EVALS_DIR = TESTS_DIR / "evals"
SKILLS_DIR = TESTS_DIR.parent / "skills"


def load_checks_module(skill_dir: Path):
    """Dynamically load a skill's checks.py as a module."""
    checks_path = skill_dir / "checks.py"
    if not checks_path.exists():
        raise FileNotFoundError(f"{checks_path} not found")
    spec = importlib.util.spec_from_file_location("checks", checks_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _skill_reference_text(skill_name: str, skill_ref: str | None) -> str:
    """Load the reference .md content a live agent must follow."""
    if not skill_ref:
        return ""
    ref_path = SKILLS_DIR / skill_name / "references" / skill_ref
    if ref_path.exists():
        return ref_path.read_text(encoding="utf-8")
    return ""


def _compose_prompt(skill_name: str, prompt: dict) -> str:
    """Build the full prompt handed to a live agent."""
    ref_text = _skill_reference_text(skill_name, prompt.get("skill_ref"))
    parts = []
    if ref_text:
        parts.append(
            "You are following this C project style/skill reference. "
            "Obey it exactly:\n\n" + ref_text
        )
    parts.append("User request:\n" + prompt["prompt"])
    if prompt.get("is_codegen"):
        parts.append(
            "Respond with the requested C code in a fenced ```c code block, "
            "following every rule in the reference above."
        )
    return "\n\n---\n\n".join(parts)


def run_agent(composed_prompt: str) -> str | None:
    """Invoke the configured agent CLI. Returns its stdout, or None on failure."""
    cmd = os.environ.get("STOLON_AGENT_CMD")
    if not cmd:
        return None
    timeout = int(os.environ.get("STOLON_AGENT_TIMEOUT", "180"))
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            input=composed_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return None
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _run_checks(checks_mod, expected, output_text, project_dir):
    """Run the expected checks against text/dir. Returns (passed, failed, skipped)."""
    passed = failed = skipped = 0
    for check_name in expected:
        fn = getattr(checks_mod, f"check_{check_name}", None)
        if fn is None:
            print(f"    - {check_name} (undefined)")
            skipped += 1
            continue

        input_type = getattr(fn, "input_type", "text")
        try:
            if input_type == "directory":
                if project_dir and project_dir.is_dir():
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


def run_skill_eval(
    skill_name: str, output_dir: Path, live: bool = False
) -> tuple[int, int, int]:
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

        output_text = ""
        project_dir = None

        if live:
            # In live mode, skip negative prompts that intentionally do not
            # trigger the skill -- there is nothing to invoke meaningfully.
            if prompt.get("should_trigger") is False:
                print("    - negative prompt (skipped in live mode)")
                skipped += len(expected)
                continue
            composed = _compose_prompt(skill_name, prompt)
            agent_out = run_agent(composed)
            if agent_out is None:
                print("    - agent produced no output (skipped)")
                skipped += len(expected)
                continue
            output_text = agent_out
            # Persist live output for inspection/debugging.
            live_dir = output_dir / eval_id
            live_dir.mkdir(parents=True, exist_ok=True)
            (live_dir / "output.txt").write_text(agent_out, encoding="utf-8")
        else:
            prompt_dir = output_dir / eval_id
            if not prompt_dir.is_dir():
                print("    - no output directory (skipped)")
                skipped += len(expected)
                continue
            output_file = prompt_dir / "output.txt"
            project_dir = prompt_dir / "project"
            if output_file.exists():
                output_text = output_file.read_text(encoding="utf-8")

        p, f, s = _run_checks(checks_mod, expected, output_text, project_dir)
        passed += p
        failed += f
        skipped += s

    return passed, failed, skipped


def main():
    args = sys.argv[1:]
    live = False
    if "--live" in args:
        live = True
        args.remove("--live")

    skill_filter = args[0] if len(args) > 0 else None
    custom_output = args[1] if len(args) > 1 else None

    if live and not os.environ.get("STOLON_AGENT_CMD"):
        print(
            "NOTE: --live requested but STOLON_AGENT_CMD is not set. "
            "Falling back to baseline mode.\n"
            "      Set STOLON_AGENT_CMD to a command that reads a prompt on "
            "stdin and writes the response to stdout."
        )
        live = False

    if skill_filter:
        skills = [skill_filter]
    else:
        skills = sorted(
            d.name for d in EVALS_DIR.iterdir()
            if d.is_dir() and d.name != "integration"
        )

    mode = "live" if live else "baseline"
    total_pass = total_fail = total_skip = 0

    for skill in skills:
        print(f"\n=== Skill: {skill} ({mode}) ===")

        if custom_output:
            out_dir = Path(custom_output)
        elif live:
            out_dir = TESTS_DIR / ".live_out" / skill
        else:
            out_dir = EVALS_DIR / skill / "baselines"

        p, f, s = run_skill_eval(skill, out_dir, live=live)
        total_pass += p
        total_fail += f
        total_skip += s

    print(f"\n===============================")
    print(f"  MODE:    {mode}")
    print(f"  PASSED:  {total_pass}")
    print(f"  FAILED:  {total_fail}")
    print(f"  SKIPPED: {total_skip}")
    print(f"===============================")

    sys.exit(1 if total_fail > 0 else 0)


if __name__ == "__main__":
    main()
