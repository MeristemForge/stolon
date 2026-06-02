---
name: c-project-build
description: >
  Use when building, compiling, testing, or running coverage for a C project,
  or when build fails, sanitizer reports errors, or coverage needs generating.
  Also use when configuring CMake, enabling sanitizers (ASAN/TSAN/UBSAN),
  generating compile_commands.json, or any cmake/ctest command is needed.
---

# C Project Build

## When NOT to Use

code style review → c-project-style, scaffolding → c-project-init, committing → c-project-commit

## STOP — Read Reference Before ANY Build Command

Read `references/build.md` in this skill's base directory. If not found, STOP and tell the user.

Before any cmake command, follow the **Inputs — MANDATORY Checks Before Build** section in `build.md`. No exceptions.

If the project pins toolchain/dependency versions (cmake, OpenSSL, compiler), resolve them FIRST per **Toolchain & Dependency Versions** in `build.md`: find the required version, pin CMake to it, ask the user if missing. Never build with the default and debug the version after it fails.

Use the platform-default compiler unless the user asks otherwise (Windows → MSVC `cl`, Linux → `gcc`, macOS/Android/iOS → `clang`); see **Default Compiler by Platform** in `build.md`.

**Skip confirmation when:**

1. **Rebuild only** — the user only changed `.c`/`.h` files AND a full configure was completed in this session. Run `cmake --build out --config {build_type}` directly.
2. **Re-run tests** — a build already succeeded in this session and the user wants to run tests again (e.g. after a code fix). Run `ctest --test-dir out -C {build_type} ...` directly.
3. **Iterative fix cycle** — the user is in a fix → rebuild → test loop within the same session. Only rebuild + test; do not re-ask build type or feature flags.

## Mandatory Post-Build Verification

After ANY build or test command, you MUST check the following. Do NOT report success until all items pass.

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **Build exit code** | cmake --build must return 0. If non-zero, report the FIRST error (not all 200 lines). |
| 2 | **Warnings** | Scan output for warnings. Report them to the user — do not silently ignore. |
| 3 | **Test results** | ctest must show 0 failures. If any test fails, report which module and the failure output. |
| 4 | **Sanitizer output** | If ASAN/TSAN/UBSAN enabled, check for ANY sanitizer report in output. A "passing" test with sanitizer errors is NOT passing. |
| 5 | **compile_commands.json** | After configure/build, copy to project root if missing or stale. |
| 6 | **vcenv.cmd (Windows)** | On Windows, verify all cmake/ctest commands ran through `out/vcenv.cmd`. |
| 7 | **Correct compiler** | Configure used the platform-default compiler (or the user's choice). Windows: every configure MUST pass `-DCMAKE_C_COMPILER=cl` (VS env alone won't stop CMake picking gcc/clang off PATH); confirm output shows `MSVC`. Linux/macOS: confirm identification matches the intended GCC/Clang. |
| 8 | **Correct toolchain/dep versions** | If the project pins versions, confirm configure output (e.g. `Found OpenSSL: ... (found version ...)`) matches the constraint, not whatever was first on PATH. |
