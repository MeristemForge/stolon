# Skill Evals

Lightweight Python eval harness for testing agent skill instructions. Each skill has its own eval suite.

## How it works

1. `prompts.json` defines prompts that simulate user requests
2. `baselines/` contains AI-generated responses (baseline)
3. `checks.py` has deterministic functions that verify responses follow skill rules
4. `run_eval.py` feeds outputs into checks and reports pass/fail

## Two ways the harness tests a skill

The harness has two complementary modes. Understanding the difference matters,
because a green baseline run does NOT mean the live agent obeys the skill.

- **Baseline mode (default)** runs checks against the committed sample answers
  in `baselines/<id>/output.txt`. Fast and deterministic, but it tests a frozen
  snapshot that was itself written to pass. It catches regressions in the
  sample answers and in the checks, not live agent behavior.

- **Live mode (`--live`)** actually invokes a real agent per prompt and runs the
  checks against ITS output. This is the only mode that measures the agent.
  It needs an agent command in `STOLON_AGENT_CMD` (reads a prompt on stdin,
  writes the response to stdout). Without it, `--live` falls back to baseline
  mode and says so.

Two further gates back the evals up with determinism instead of keyword greps:

- **`lint_c.py`** is a real C linter (state-machine scan, not naive grep) that
  hard-enforces the mechanical style rules (ASCII only, no `//`, `_Pragma`,
  banned functions, license header, platform `#ifdef` placement) on actual
  `.c`/`.h` files. These rules are guaranteed by tooling, not by the agent
  remembering them.

- **`run_coverage.py`** is a meta-gate: it parses the numbered rule headings in
  each skill reference and asserts every rule maps to a check or an explicit
  waiver. A new rule with no coverage fails the gate, so coverage cannot drift
  silently (the logging rule once sat uncovered for exactly this reason).

## Structure

```
tests/
├── run_eval.py              # Universal eval runner (baseline + --live modes)
├── run_smoke.py             # Live smoke tests against real projects
├── run_integration.py       # Cross-skill handoff validation
├── run_regression.py        # Baseline diff against git ref
├── run_diff.py              # Quick baseline diff tool
├── run_coverage.py          # Rule-coverage gate (every rule needs a check/waiver)
├── lint_c.py                # Deterministic C style linter (real .c/.h files)
├── README.md
└── evals/
    ├── c-project-init/      # One directory per skill
    │   ├── prompts.json     # Prompt definitions + expected checks
    │   ├── checks.py        # Deterministic check functions
    │   └── baselines/       # AI-generated baseline outputs
    ├── c-project-build/
    ├── c-project-debug/
    ├── c-project-commit/
    ├── c-project-style/
    └── integration/         # Cross-skill checks
```

## Usage

```bash
# Run all skill evals (baseline mode)
python tests/run_eval.py

# Run one skill eval
python tests/run_eval.py c-project-build

# Run one skill eval with custom output directory
python tests/run_eval.py c-project-build path/to/outputs

# Run against a LIVE agent (set STOLON_AGENT_CMD first)
export STOLON_AGENT_CMD="myagent --quiet"   # reads prompt on stdin -> response on stdout
python tests/run_eval.py --live
python tests/run_eval.py --live c-project-style

# Rule coverage gate (fails if any rule heading has no check/waiver)
python tests/run_coverage.py
python tests/run_coverage.py c-project-style

# Deterministic C linter on real source files
python tests/lint_c.py --project path/to/c-project
python tests/lint_c.py src/foo.c include/foo.h
# bundled third-party libs in non-standard folders: exclude by name
python tests/lint_c.py --project path/to/c-project --exclude minicoro,llhttp

# Build/sanitizer smoke against your OWN project (project-agnostic)
python tests/run_smoke.py build --project path/to/c-project
#   or: set STOLON_SMOKE_PROJECT=path/to/c-project

# Run smoke tests (requires real project)
python tests/run_smoke.py
python tests/run_smoke.py init

# Run integration tests (cross-skill)
python tests/run_integration.py

# Diff baselines against git ref
python tests/run_regression.py
python tests/run_regression.py c-project-build --ref HEAD~3
```

## Workflow after changing skill instructions

1. Modify skill references (e.g. `skills/c-project-build/references/build.md`)
2. Ask the AI to re-read the updated skill instructions and regenerate sample-outputs
3. Run `python tests/run_eval.py` to verify checks still pass
4. Run `python tests/run_coverage.py` to confirm every rule still maps to a check or waiver
5. Run `python tests/run_regression.py` to see what changed in baselines
6. If checks fail, either fix the skill instructions or update checks.py
7. If you added a new numbered rule, add a check (or a waiver) and map it in `run_coverage.py`
8. Commit the updated baselines as the new baseline

## Adding a new skill eval

1. Create `tests/evals/<skill-name>/`
2. Add `prompts.json` — array of prompts with `id`, `skill_ref`, `expected_checks`
3. Add `checks.py` — functions named `check_<name>` decorated with `@directory_check` or `@text_check`
4. Ask the AI to read the skill instructions and generate responses for each prompt
5. Save AI responses into `baselines/<prompt-id>/output.txt` (text) or `baselines/<prompt-id>/project/` (directory)
6. Run: `python tests/run_eval.py <skill-name>` (e.g. `python tests/run_eval.py c-project-style`)
7. Commit baselines

## Writing checks

```python
from pathlib import Path

def directory_check(fn):
    fn.input_type = "directory"
    return fn

def text_check(fn):
    fn.input_type = "text"
    return fn

@directory_check
def check_has_cmakelists(d: Path) -> bool:
    return (d / "CMakeLists.txt").exists()

@text_check
def check_mentions_asan(text: str) -> bool:
    return "ASAN" in text.upper()
```

- `@directory_check`: receives a `Path` to the generated project directory
- `@text_check`: receives the agent's text response as a string
- Return `True` for pass, `False` for fail
