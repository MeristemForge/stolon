---
name: c-project-commit
description: >
  Use when staging, committing, or pushing code changes in a C project.
  Also use when amending commits, squashing, writing commit messages,
  or any git add/commit/push operation in the project.
---

# C Project Commit

## When NOT to Use

building/testing → c-project-build, writing code → c-project-style

## STOP — Read Reference Before ANY Git Command

Read `references/commit.md` in this skill's base directory. If not found, STOP and tell the user.

## Mandatory Pre-Commit Verification

Before ANY `git commit`, you MUST verify the following. Do NOT commit until all items pass.

Build and test are **not** part of this checklist. Assume the user has already built and tested the code before asking to commit — do NOT rebuild or run tests unless the user explicitly asks, or the staged diff clearly shows broken/incomplete code (e.g. syntax errors, unbalanced braces). If you have doubts about correctness, ask the user rather than silently kicking off a build.

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **Diff review** | Run `git diff --staged` and read every changed line. No debug leftovers (`fprintf(stderr, "DEBUG`), no TODO/FIXME introduced, no commented-out code. |
| 2 | **Style compliance** | All staged `.c`/`.h` files must pass the c-project-style checklist (invoke it if not already done this session). |
| 3 | **Commit message** | Format: `<type>(<scope>): <summary>`. Imperative mood, lowercase, no period, max 72 chars. |
| 4 | **No secrets/binaries** | Check staged files for `.exe`, `.o`, `.dll`, credentials, keys. Do NOT commit build artifacts. |
| 5 | **Scope accuracy** | The `<scope>` must match the actual module(s) changed. Multi-module changes: omit scope or use the dominant module. |
