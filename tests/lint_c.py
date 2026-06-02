#!/usr/bin/env python3
"""Deterministic C style linter for stolon.

Enforces the mechanically-checkable rules from c-project-style/references/style.md.
Unlike the eval harness (which greps agent *text*), this linter scans real .c/.h
files and is a hard, regex/state-machine gate that does not depend on the agent
remembering anything. These are the rules a linter can guarantee:

  - ASCII only                  (style.md S14.1)
  - No // line comments         (style.md S14.4)
  - _Pragma("once"), no #ifndef (style.md S3)
  - No banned functions         (style.md S18)
  - License header present      (style.md S1)
  - No platform #ifdef outside src/platform/ (style.md S12)

A tiny C scanner classifies each character as code / line-comment /
block-comment / string / char-literal so that // inside a string or a
URL ("http://") and banned names inside comments are NOT false positives.

Usage:
    python lint_c.py <path> [<path> ...]   # lint files or directories
    python lint_c.py --project <dir>       # lint all .c/.h under a project
    python lint_c.py --project <dir> --exclude llhttp,foo   # extra excludes

Third-party / bundled code is skipped by default (style.md S23 exempts it):
any path segment in DEFAULT_EXCLUDES is ignored. Add more with --exclude.

Exit code 0 when clean, 1 when any violation is found.
"""

import re
import sys
from pathlib import Path

# --- third-party / generated dirs skipped by default (style.md S23) -------
# Bundled libraries live in their own subdirectory and keep upstream style.
DEFAULT_EXCLUDES = {
    "third_party",
    "third-party",
    "thirdparty",
    "vendor",
    "external",
    "deps",
    "build",
    "out",
    ".git",
    # Known bundled libs seen in target projects.
    "minicoro",
    "llhttp",
    "tiny-AES-c",
    "tiny-aes-c",
    "tomlc99",
    "wepoll",
}

# --- banned functions (style.md S18) -------------------------------------

BANNED_FUNCTIONS = (
    "sprintf",
    "strcpy",
    "strcat",
    "gets",
    "atoi",
    "atof",
    "atol",
    "strtok",
    "strerror",
    "localtime",
    "gmtime",
    "ctime",
    "asctime",
)

# State labels produced by the scanner for each character.
CODE = "code"
LINE_COMMENT = "line_comment"
BLOCK_COMMENT = "block_comment"
STRING = "string"
CHAR = "char"


class Violation:
    def __init__(self, path: Path, line: int, rule: str, detail: str):
        self.path = path
        self.line = line
        self.rule = rule
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.detail}"


def classify(text: str) -> list[str]:
    """Return a per-character state label for the whole file.

    Tracks code / line comment / block comment / string / char literal so
    callers can ignore // and banned names that appear inside comments or
    string/char literals.
    """
    states = [CODE] * len(text)
    state = CODE
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == CODE:
            if c == "/" and nxt == "/":
                state = LINE_COMMENT
            elif c == "/" and nxt == "*":
                state = BLOCK_COMMENT
                states[i] = BLOCK_COMMENT
                if i + 1 < n:
                    states[i + 1] = BLOCK_COMMENT
                i += 2
                continue
            elif c == '"':
                state = STRING
            elif c == "'":
                state = CHAR
            states[i] = CODE if state == CODE else state
            # For // we want the two slashes themselves flagged as code so the
            # detector can see them; mark current as the new state instead.
            if state == LINE_COMMENT:
                states[i] = LINE_COMMENT
            i += 1
            continue

        if state == LINE_COMMENT:
            states[i] = LINE_COMMENT
            if c == "\n":
                state = CODE
            i += 1
            continue

        if state == BLOCK_COMMENT:
            states[i] = BLOCK_COMMENT
            if c == "*" and nxt == "/":
                if i + 1 < n:
                    states[i + 1] = BLOCK_COMMENT
                i += 2
                state = CODE
                continue
            i += 1
            continue

        if state == STRING:
            states[i] = STRING
            if c == "\\":
                if i + 1 < n:
                    states[i + 1] = STRING
                i += 2
                continue
            if c == '"':
                state = CODE
            i += 1
            continue

        if state == CHAR:
            states[i] = CHAR
            if c == "\\":
                if i + 1 < n:
                    states[i + 1] = CHAR
                i += 2
                continue
            if c == "'":
                state = CODE
            i += 1
            continue

    return states


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def lint_text(path: Path, text: str, rel_posix: str) -> list[Violation]:
    """Run all deterministic checks against one file's text."""
    violations: list[Violation] = []
    states = classify(text)

    # --- S14.1 ASCII only (entire file, including comments and strings) ---
    for i, ch in enumerate(text):
        if ord(ch) > 0x7F:
            violations.append(
                Violation(
                    path,
                    _line_of(text, i),
                    "ascii-only",
                    f"non-ASCII char U+{ord(ch):04X} ({ch!r})",
                )
            )
            break  # one report per file is enough to flag it

    # --- S14.4 no // line comments (only when in CODE-turned-line-comment) ---
    for i in range(len(text) - 1):
        if text[i] == "/" and text[i + 1] == "/" and states[i] == LINE_COMMENT:
            # states[i] is LINE_COMMENT only when the // started in code.
            violations.append(
                Violation(
                    path,
                    _line_of(text, i),
                    "cpp-comment",
                    "// line comment; use /* ... */",
                )
            )

    # --- S3 header guards: .h must use _Pragma("once"), not #ifndef/#pragma once
    if path.suffix == ".h":
        if '_Pragma("once")' not in text:
            violations.append(
                Violation(path, 1, "header-guard", '.h missing _Pragma("once")')
            )
        if "#pragma once" in text:
            line = _line_of(text, text.index("#pragma once"))
            violations.append(
                Violation(path, line, "header-guard", 'use _Pragma("once"), not #pragma once')
            )
        m = re.search(r"^\s*#\s*ifndef\b", text, re.MULTILINE)
        if m and re.search(r"^\s*#\s*define\b", text, re.MULTILINE):
            # Heuristic: a classic include guard pair. _Pragma is the rule.
            violations.append(
                Violation(
                    path,
                    _line_of(text, m.start()),
                    "header-guard",
                    "#ifndef/#define guard; use _Pragma(\"once\")",
                )
            )

    # --- S18 banned functions (in CODE only) ---
    for fn in BANNED_FUNCTIONS:
        for m in re.finditer(r"\b" + re.escape(fn) + r"\s*\(", text):
            if states[m.start()] == CODE:
                violations.append(
                    Violation(
                        path,
                        _line_of(text, m.start()),
                        "banned-function",
                        f"{fn}() is banned (style.md S18)",
                    )
                )

    # --- S1 license header: file must start with a /** ... */ block ---
    stripped = text.lstrip()
    if not stripped.startswith("/*"):
        violations.append(
            Violation(path, 1, "license-header", "file must start with /** license */ block")
        )

    # --- S12 platform conditionals only under src/platform/ ---
    path_parts = set(re.split(r"[\\/]", rel_posix))
    if "platform" not in path_parts:
        for m in re.finditer(r"#\s*if(?:def|ndef)?\b[^\n]*", text):
            seg = m.group(0)
            if states[m.start()] != CODE:
                continue
            if re.search(r"_WIN32|_WIN64|__linux__|__APPLE__|__unix__|_MSC_VER", seg):
                violations.append(
                    Violation(
                        path,
                        _line_of(text, m.start()),
                        "platform-ifdef",
                        "platform conditional outside src/platform/",
                    )
                )

    return violations


def iter_c_files(root: Path, excludes: set[str]):
    if root.is_file():
        if root.suffix in (".c", ".h") and root.name != ".gitkeep":
            yield root
        return
    for f in sorted(root.rglob("*")):
        if f.suffix not in (".c", ".h") or f.name == ".gitkeep" or not f.is_file():
            continue
        # Skip any file whose path passes through an excluded directory.
        if any(part in excludes for part in f.parts):
            continue
        yield f


def lint_paths(
    paths: list[Path], root: Path | None = None, excludes: set[str] | None = None
) -> list[Violation]:
    excludes = excludes if excludes is not None else set(DEFAULT_EXCLUDES)
    violations: list[Violation] = []
    for p in paths:
        for f in iter_c_files(p, excludes):
            try:
                raw = f.read_bytes()
            except OSError as e:
                violations.append(Violation(f, 0, "io-error", str(e)))
                continue
            # Decode as latin-1 so non-ASCII bytes survive for the ASCII check.
            text = raw.decode("latin-1")
            base = root if root else (p if p.is_dir() else p.parent)
            try:
                rel_posix = f.relative_to(base).as_posix()
            except ValueError:
                rel_posix = f.as_posix()
            violations.extend(lint_text(f, text, rel_posix))
    return violations


def main():
    args = sys.argv[1:]
    root = None
    excludes = set(DEFAULT_EXCLUDES)

    # Pull out --exclude name1,name2 anywhere in the args.
    if "--exclude" in args:
        idx = args.index("--exclude")
        if idx + 1 >= len(args):
            print("usage: lint_c.py ... --exclude name1,name2")
            sys.exit(2)
        excludes |= {x.strip() for x in args[idx + 1].split(",") if x.strip()}
        del args[idx:idx + 2]

    if args and args[0] == "--project":
        if len(args) < 2:
            print("usage: lint_c.py --project <dir>")
            sys.exit(2)
        root = Path(args[1])
        targets = [root]
    elif args:
        targets = [Path(a) for a in args]
    else:
        print(__doc__)
        sys.exit(2)

    violations = lint_paths(targets, root, excludes)

    if violations:
        for v in violations:
            print(v)
        print(f"\n{len(violations)} violation(s) found")
        sys.exit(1)
    else:
        print("clean: no style violations")
        sys.exit(0)


if __name__ == "__main__":
    main()
