#!/usr/bin/env python3
"""Rule coverage gate for stolon skill evals.

Problem this solves: eval coverage drifts. A rule can live in a skill's
reference .md for months with no check guarding it (the logging rule did
exactly that). This meta-test parses the numbered rule headings from each
skill reference and asserts every rule is either:

  - COVERED  -- at least one eval check is mapped to it, or
  - WAIVED   -- explicitly listed with a reason (e.g. enforced by lint_c.py,
                or not mechanically checkable in text).

A new rule heading added to a reference with no mapping fails the gate,
forcing the author to add a check or a waiver. Unknown mappings (pointing at
a rule number that no longer exists) also fail, so stale mappings get cleaned.

Usage:
    python run_coverage.py            # check all configured skills
    python run_coverage.py c-project-style
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
EVALS_DIR = TESTS_DIR / "evals"
SKILLS_DIR = TESTS_DIR.parent / "skills"

# For each skill: which reference file holds the numbered rules, and a map of
# "rule number" -> coverage. Coverage is either a list of check names that
# guard the rule, or {"waived": "reason"}.
#
# Rule numbers match the "## N. Title" headings in the reference file.
COVERAGE = {
    "c-project-style": {
        "reference": "references/style.md",
        "rules": {
            "1": {"waived": "license header enforced deterministically by lint_c.py"},
            "2": {"waived": "language standard is a CMake/build concern, see c-project-build"},
            "3": ["recommends_pragma_once", "no_ifndef_guards", "rejects_pragma_once_raw"],
            "4": {"waived": "extern keyword is verified by compiler, low agent-error rate"},
            "5": ["mentions_own_header_first", "mentions_grouped_includes", "mentions_stdlib_last"],
            "6": ["mentions_public_header_path", "mentions_src_implementation", "mentions_test_file"],
            "7": [
                "public_func_has_project_prefix",
                "public_func_has_module_segment",
                "public_func_uses_snake_case",
                "static_cb_has_underscore_prefix",
                "static_cb_has_cb_suffix",
                "static_cb_no_project_prefix",
            ],
            "8": {"waived": "type rules verified by compiler warnings, not text-checkable"},
            "9": ["mentions_create_destroy_for_opaque"],
            "10": [
                "mentions_create_destroy_for_opaque",
                "mentions_init_deinit_for_caller_owned",
                "mentions_malloc_ownership",
            ],
            "11": {"waived": "file organization is structural, checked via init scaffold"},
            "12": [
                "platform_code_in_platform_dir",
                "no_ifdefs_outside_platform",
                "mentions_platform_prefix",
            ],
            "13": {"waived": "formatting enforced by .clang-format, not by the agent"},
            "14": [
                "uses_c_style_comments",
                "no_cpp_style_comments",
                "mentions_ascii_only",
                "rejects_cpp_comments",
            ],
            "15": {"waived": "unused-param rule verified by compiler -Wunused"},
            "16": [
                "mentions_create_destroy_for_opaque",
                "mentions_malloc_ownership",
            ],
            "17": [
                "log_uses_module_tag",
                "log_uses_loge",
                "log_is_key_value_style",
                "log_not_sentence_style",
            ],
            "18": ["bans_sprintf", "bans_strcpy", "recommends_snprintf"],
            "19": {"waived": "intrusive DS pattern is advanced, low agent-error rate"},
            "20": {"waived": "C11 _Generic is advanced/rare, not a common edit"},
            "21": [
                "uses_custom_assert",
                "no_standard_assert",
                "one_concern_per_test",
                "no_global_state_in_tests",
                "mentions_add_test_helper",
            ],
            "22": [
                "mentions_add_to_srcs",
                "mentions_umbrella_header",
                "mentions_add_test_cmake",
            ],
            "23": {"waived": "third-party bundling guidance, not a per-edit rule"},
        },
    },
}


def load_check_names(skill: str) -> set[str]:
    """Collect every check_<name> defined in a skill's checks.py."""
    checks_path = EVALS_DIR / skill / "checks.py"
    if not checks_path.exists():
        return set()
    spec = importlib.util.spec_from_file_location(f"{skill}_checks", checks_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {
        name[len("check_"):]
        for name in dir(mod)
        if name.startswith("check_") and callable(getattr(mod, name))
    }


def parse_rule_numbers(reference_path: Path) -> list[tuple[str, str]]:
    """Return [(number, title)] for every '## N. Title' heading."""
    rules = []
    for line in reference_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(\d+)\.\s+(.+?)\s*$", line)
        if m:
            rules.append((m.group(1), m.group(2)))
    return rules


def check_skill(skill: str) -> tuple[int, int, list[str]]:
    """Returns (covered, problems, messages)."""
    cfg = COVERAGE[skill]
    reference_path = SKILLS_DIR / skill / cfg["reference"]
    if not reference_path.exists():
        return 0, 1, [f"  reference not found: {reference_path}"]

    rules = parse_rule_numbers(reference_path)
    mapping = cfg["rules"]
    check_names = load_check_names(skill)

    covered = 0
    problems = 0
    messages = []

    doc_numbers = {num for num, _ in rules}

    # 1. Every rule heading in the doc must have a mapping entry.
    for num, title in rules:
        entry = mapping.get(num)
        if entry is None:
            problems += 1
            messages.append(
                f"  [UNMAPPED] rule {num} ({title}) has no coverage entry "
                f"-- add a check or a waiver in run_coverage.py"
            )
            continue
        if isinstance(entry, dict) and "waived" in entry:
            covered += 1
            messages.append(f"  [WAIVED]   rule {num} ({title}): {entry['waived']}")
            continue
        if isinstance(entry, list):
            missing = [c for c in entry if c not in check_names]
            if not entry:
                problems += 1
                messages.append(f"  [EMPTY]    rule {num} ({title}) maps to no checks")
            elif missing:
                problems += 1
                messages.append(
                    f"  [MISSING]  rule {num} ({title}) maps to undefined check(s): "
                    f"{', '.join(missing)}"
                )
            else:
                covered += 1
                messages.append(
                    f"  [COVERED]  rule {num} ({title}) -> {len(entry)} check(s)"
                )
            continue
        problems += 1
        messages.append(f"  [BAD]      rule {num} ({title}) has malformed mapping")

    # 2. Every mapping entry must point at a rule that still exists.
    for num in mapping:
        if num not in doc_numbers:
            problems += 1
            messages.append(
                f"  [STALE]    mapping for rule {num} but no such heading in {cfg['reference']}"
            )

    return covered, problems, messages


def main():
    skill_filter = sys.argv[1] if len(sys.argv) > 1 else None
    skills = [skill_filter] if skill_filter else sorted(COVERAGE.keys())

    total_covered = 0
    total_problems = 0

    for skill in skills:
        if skill not in COVERAGE:
            print(f"\n=== {skill} ===")
            print(f"  no coverage config for {skill} (add it to run_coverage.py)")
            total_problems += 1
            continue
        print(f"\n=== Coverage: {skill} ===")
        covered, problems, messages = check_skill(skill)
        for m in messages:
            print(m)
        total_covered += covered
        total_problems += problems

    print(f"\n===============================")
    print(f"  COVERED:  {total_covered}")
    print(f"  PROBLEMS: {total_problems}")
    print(f"===============================")

    if total_problems:
        print("\nRule coverage gate FAILED. Every rule heading needs a check or a waiver.")
        sys.exit(1)
    print("\nRule coverage gate passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
