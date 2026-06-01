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

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **Diff review** | Run `git diff --staged` and read every changed line. No debug leftovers (`fprintf(stderr, "DEBUG`), no TODO/FIXME introduced, no commented-out code. |
| 2 | **Build passes** | The project must build without errors. If you just edited code, rebuild first. |
| 3 | **Tests pass** | Run `ctest` for affected modules. Do NOT commit code that breaks tests. |
| 4 | **Style compliance** | All staged `.c`/`.h` files must pass the c-project-style checklist (invoke it if not already done this session). |
| 5 | **Commit message** | Format: `<type>(<scope>): <summary>`. Imperative mood, lowercase, no period, max 72 chars. |
| 6 | **No secrets/binaries** | Check staged files for `.exe`, `.o`, `.dll`, credentials, keys. Do NOT commit build artifacts. |
| 7 | **Scope accuracy** | The `<scope>` must match the actual module(s) changed. Multi-module changes: omit scope or use the dominant module. |
