---
name: c-project-debug
description: >
  Use when a C executable crashes, segfaults, aborts, hangs, or produces
  unexpected behavior. Use when investigating SIGSEGV, SIGABRT, use-after-free,
  double-free, null pointer dereference, or memory corruption in a CMake/Ninja
  C project. Also use when a test fails unexpectedly, when you need to attach
  a debugger, or when diagnosing why a program produces wrong output.
---

# C Project Debug

## When NOT to Use

build failures → c-project-build, code style → c-project-style

## STOP — Read Reference Before ANY Debug Action

Read `references/debug.md` in this skill's base directory. If not found, STOP and tell the user.

Follow the three-tier strategy in `debug.md` (reproduce → sanitizers → debugger). No shortcuts.

## Mandatory Debug Verification

After proposing or applying a fix, you MUST verify it. Do NOT report "fixed" until all items pass.

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **Reproduces first** | You must see the failure BEFORE fixing. No blind fixes. |
| 2 | **Build clean** | Rebuild after fix — zero errors, zero new warnings. |
| 3 | **Test passes** | The failing test now passes: `ctest -R {module} --output-on-failure`. |
| 4 | **Sanitizer clean** | Rebuild with ASAN and re-run. Zero sanitizer reports. A fix that passes tests but triggers ASAN is NOT a fix. |
| 5 | **No regressions** | Run the full test suite, not just the fixed module. |
| 6 | **Debug logs removed** | No `fprintf(stderr, "DEBUG` or temporary prints left in the code. |
| 7 | **Root cause stated** | Explain the root cause in one sentence before reporting done. "It works now" is not acceptable. |
