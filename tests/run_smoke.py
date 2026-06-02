#!/usr/bin/env python3
"""Live smoke test framework for stolon skills.

Unlike evals (which test static baselines), smoke tests verify that
skill instructions produce correct behavior when executed against a
real project. Each smoke test:

1. Sets up a scenario (e.g., scaffold a project, create a build)
2. Simulates the skill workflow steps
3. Verifies the actual result (files exist, build succeeds, etc.)

Usage:
    python run_smoke.py                    # run all smoke tests
    python run_smoke.py init               # run one category
    python run_smoke.py --project /path    # use existing project
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent


class SmokeResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: list[str] = []
        self.failed: list[str] = []

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed.append(name)
            print(f"    [PASS] {name}")
        else:
            self.failed.append(name)
            msg = f"    [FAIL] {name}"
            if detail:
                msg += f" ({detail})"
            print(msg)


def run_cmd(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=cwd, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, returncode=-1, stdout="", stderr="TIMEOUT"
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            cmd, returncode=-1, stdout="", stderr=str(e)
        )


def find_cmake() -> str | None:
    """Find cmake executable."""
    return shutil.which("cmake")


def find_ninja() -> str | None:
    """Find ninja executable."""
    return shutil.which("ninja")


# ============================================================
# Smoke test: init -> build chain
# ============================================================

def smoke_init_build_chain(project_dir: Path | None = None) -> SmokeResult:
    """Verify that a scaffolded project from init baselines can actually build.

    Uses the setup_lib_basic baseline project directory.
    """
    result = SmokeResult("init_build_chain")
    print(f"\n  --- {result.name} ---")

    baseline_project = (
        TESTS_DIR / "evals" / "c-project-init" / "baselines"
        / "setup_lib_basic" / "project"
    )

    if not baseline_project.is_dir():
        result.check("baseline_exists", False, "setup_lib_basic/project not found")
        return result

    result.check("baseline_exists", True)

    # Copy to temp dir for building
    with tempfile.TemporaryDirectory(prefix="stolon_smoke_") as tmpdir:
        tmp_project = Path(tmpdir) / "project"
        shutil.copytree(baseline_project, tmp_project)

        cmake = find_cmake()
        ninja = find_ninja()

        result.check("cmake_available", cmake is not None, "cmake not found on PATH")
        result.check("ninja_available", ninja is not None, "ninja not found on PATH")

        if not cmake or not ninja:
            return result

        # Configure
        configure_cmd = [
            cmake, "-B", "out", "-G", "Ninja Multi-Config",
            "-DNETKIT_ENABLE_TESTING=ON",
        ]
        r = run_cmd(configure_cmd, tmp_project)
        result.check(
            "configure_succeeds",
            r.returncode == 0,
            r.stderr[:200] if r.returncode != 0 else "",
        )

        if r.returncode != 0:
            return result

        # Build
        build_cmd = [cmake, "--build", "out", "--config", "Debug"]
        r = run_cmd(build_cmd, tmp_project)
        result.check(
            "build_succeeds",
            r.returncode == 0,
            r.stderr[:200] if r.returncode != 0 else "",
        )

        # Check compile_commands.json exists
        result.check(
            "compile_commands_generated",
            (tmp_project / "out" / "compile_commands.json").exists(),
        )

        if r.returncode != 0:
            return result

        # Test
        test_cmd = [
            "ctest", "--test-dir", "out", "-C", "Debug",
            "--output-on-failure",
        ]
        r = run_cmd(test_cmd, tmp_project)
        result.check(
            "tests_pass",
            r.returncode == 0,
            r.stdout[:200] if r.returncode != 0 else "",
        )

    return result


# ============================================================
# Smoke test: build sanitizer workflow
# ============================================================

def smoke_build_sanitizer(project_dir: Path | None = None) -> SmokeResult:
    """Verify that the ASAN build workflow from build skill actually works.

    Uses the Xylem project if available, otherwise skips.
    """
    result = SmokeResult("build_sanitizer_workflow")
    print(f"\n  --- {result.name} ---")

    if project_dir and (project_dir / "CMakeLists.txt").exists():
        target = project_dir
    else:
        # Try to find Xylem project
        candidates = [
            REPO_ROOT.parent / "Xylem",
            Path.home() / "Desktop" / "workspace" / "Xylem",
        ]
        target = None
        for c in candidates:
            if (c / "CMakeLists.txt").exists():
                target = c
                break

    if not target:
        result.check("project_found", False, "No buildable project found")
        return result

    result.check("project_found", True)

    cmake = find_cmake()
    if not cmake:
        result.check("cmake_available", False)
        return result

    # Verify CMakeLists.txt has ASAN option
    cm_text = (target / "CMakeLists.txt").read_text(encoding="utf-8")
    result.check("has_asan_option", "ENABLE_ASAN" in cm_text)
    result.check("has_testing_option", "ENABLE_TESTING" in cm_text)

    return result


# ============================================================
# Smoke test: style compliance of init output
# ============================================================

def smoke_style_compliance() -> SmokeResult:
    """Verify that init baseline code passes style checks."""
    result = SmokeResult("style_compliance")
    print(f"\n  --- {result.name} ---")

    baseline_project = (
        TESTS_DIR / "evals" / "c-project-init" / "baselines"
        / "setup_lib_basic" / "project"
    )

    if not baseline_project.is_dir():
        result.check("baseline_exists", False)
        return result

    result.check("baseline_exists", True)

    # Check all .h files use _Pragma("once")
    h_files = list(baseline_project.rglob("*.h"))
    pragma_ok = True
    for f in h_files:
        if f.name == ".gitkeep":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "#pragma once" in text:
            pragma_ok = False
            break
    result.check("no_raw_pragma_once", pragma_ok)

    # Check no // comments
    cpp_comment_ok = True
    for f in list(baseline_project.rglob("*.c")) + list(baseline_project.rglob("*.h")):
        if f.name == ".gitkeep":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("//"):
                cpp_comment_ok = False
                break
        if not cpp_comment_ok:
            break
    result.check("no_cpp_comments", cpp_comment_ok)

    # Check license headers
    license_ok = True
    for f in list(baseline_project.rglob("*.c")) + list(baseline_project.rglob("*.h")):
        if f.name == ".gitkeep":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore").lstrip()
        if not text.startswith("/**"):
            license_ok = False
            break
    result.check("all_have_license_headers", license_ok)

    # Check no banned functions
    banned_ok = True
    import re
    for f in list(baseline_project.rglob("*.c")) + list(baseline_project.rglob("*.h")):
        if f.name == ".gitkeep":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"\bsprintf\s*\(", text) or re.search(r"\bstrcpy\s*\(", text):
            banned_ok = False
            break
    result.check("no_banned_functions", banned_ok)

    return result


# ============================================================
# Smoke test: commit message format
# ============================================================

def smoke_commit_format() -> SmokeResult:
    """Verify that commit baselines produce valid conventional commit messages."""
    import re

    result = SmokeResult("commit_format_validation")
    print(f"\n  --- {result.name} ---")

    baselines_dir = TESTS_DIR / "evals" / "c-project-commit" / "baselines"
    if not baselines_dir.is_dir():
        result.check("baselines_exist", False)
        return result

    commit_pattern = re.compile(
        r'(feat|fix|refactor|test|docs|chore|perf)\([a-z]+\):\s+[a-z]'
    )

    for baseline_dir in sorted(baselines_dir.iterdir()):
        if not baseline_dir.is_dir():
            continue
        output_file = baseline_dir / "output.txt"
        if not output_file.exists():
            continue

        text = output_file.read_text(encoding="utf-8")
        name = baseline_dir.name

        if name == "negative_unrelated" or name == "commit_message_format":
            continue

        has_commit = "git commit" in text
        if has_commit:
            has_conventional = bool(commit_pattern.search(text))
            result.check(
                f"{name}_conventional_format",
                has_conventional,
                "commit message doesn't match type(scope): summary" if not has_conventional else "",
            )

    return result


# ============================================================
# Smoke test: deterministic linter on generated code
# ============================================================

def smoke_lint_generated() -> SmokeResult:
    """Run the deterministic C linter against generated baseline code.

    This is the hard gate: real .c/.h files from the init scaffold and the
    style codegen baselines must pass lint_c.py with zero violations.
    """
    import importlib.util

    result = SmokeResult("lint_generated")
    print(f"\n  --- {result.name} ---")

    lint_path = TESTS_DIR / "lint_c.py"
    if not lint_path.exists():
        result.check("linter_exists", False, "lint_c.py not found")
        return result
    result.check("linter_exists", True)

    spec = importlib.util.spec_from_file_location("lint_c", lint_path)
    lint_c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint_c)

    # 1. init scaffolds must be lint-clean.
    init_baselines = TESTS_DIR / "evals" / "c-project-init" / "baselines"
    for proj in sorted(init_baselines.glob("*/project")):
        violations = lint_c.lint_paths([proj], proj)
        result.check(
            f"init_{proj.parent.name}_clean",
            not violations,
            f"{len(violations)} violation(s)" if violations else "",
        )

    # 2. style codegen baselines: extract code blocks and lint them.
    style_baselines = TESTS_DIR / "evals" / "c-project-style" / "baselines"
    code_re = re.compile(r"```(?:c|cpp|C)?\s*\n(.*?)```", re.DOTALL)
    for out_file in sorted(style_baselines.glob("codegen_*/output.txt")):
        text = out_file.read_text(encoding="utf-8")
        blocks = code_re.findall(text)
        code = "\n".join(blocks)
        if not code.strip():
            result.check(f"{out_file.parent.name}_has_code", False, "no code block")
            continue
        # Lint the extracted code as a synthetic .c (header rules need .h).
        suffix = ".h" if "_Pragma" in code or "header" in out_file.parent.name else ".c"
        tmp = Path(tempfile.gettempdir()) / f"stolon_codegen{suffix}"
        tmp.write_text(code, encoding="utf-8")
        violations = lint_c.lint_paths([tmp])
        # Codegen snippets are partial (no license header by design for .c
        # impl snippets), so only fail on the hard mechanical rules.
        hard = [v for v in violations if v.rule in
                ("cpp-comment", "ascii-only", "banned-function")]
        result.check(
            f"{out_file.parent.name}_clean",
            not hard,
            "; ".join(str(v) for v in hard) if hard else "",
        )
        tmp.unlink(missing_ok=True)

    return result


# ============================================================
# Main
# ============================================================

SMOKE_TESTS = {
    "init": [smoke_init_build_chain, smoke_style_compliance],
    "build": [smoke_build_sanitizer],
    "commit": [smoke_commit_format],
    "lint": [smoke_lint_generated],
}


def main():
    parser = argparse.ArgumentParser(description="Live smoke tests for stolon skills")
    parser.add_argument("category", nargs="?", help="Test category (init/build/commit)")
    parser.add_argument("--project", type=Path, help="Path to a real C project for build tests")
    args = parser.parse_args()

    if args.category:
        categories = {args.category: SMOKE_TESTS.get(args.category, [])}
        if not categories[args.category]:
            print(f"Unknown category: {args.category}")
            print(f"Available: {', '.join(SMOKE_TESTS.keys())}")
            sys.exit(1)
    else:
        categories = SMOKE_TESTS

    total_passed = 0
    total_failed = 0
    results: list[SmokeResult] = []

    for cat_name, tests in categories.items():
        print(f"\n=== Smoke: {cat_name} ===")
        for test_fn in tests:
            if test_fn == smoke_build_sanitizer:
                r = test_fn(args.project)
            elif test_fn == smoke_init_build_chain:
                r = test_fn(args.project)
            else:
                r = test_fn()
            results.append(r)
            total_passed += len(r.passed)
            total_failed += len(r.failed)

    print(f"\n===============================")
    print(f"  PASSED:  {total_passed}")
    print(f"  FAILED:  {total_failed}")
    print(f"===============================")

    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
