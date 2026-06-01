---
name: c-project-style
description: >
  Use when writing, reviewing, or modifying any .c or .h file in a C project.
  Use before creating new modules, refactoring existing code, or reviewing pull
  requests for style compliance. Also use when naming functions, choosing types,
  adding structs/enums, writing comments, organizing includes, or any decision
  about how C code should look or be structured.
---

# C Project Style

## When NOT to Use

build/CMake → c-project-build, scaffolding → c-project-init, committing → c-project-commit

## STOP — Read Reference Before Writing or Reviewing ANY Code

Read `references/style.md` in this skill's base directory. If not found, STOP and tell the user.

## Mandatory Post-Edit Verification

After writing or editing ANY `.c` or `.h` file, you MUST check every modified/added line against the checklist below. Do NOT report the task as done until all violations are fixed.

### Checklist (ordered by frequency of violation)

| # | Rule | What to check |
|---|------|---------------|
| 1 | **Naming §7** | Public: `<project>_<module>_<action>`. Static: `_<module>_<action>`. Callbacks: `_<module>_<subject>_<event>_cb`. Types: `_t` suffix. Enums: `_e` tag, `_t` typedef, `UPPER` values. |
| 2 | **Comments §14** | ASCII only (no `//`, no unicode). Single-line: `/* why */`. Multi-line: `/** ... */` (opening/closing on own lines). All `.h` declarations: `/** @brief ... */`. Concise — only explain WHY, delete any comment that restates the code or adds no information. Struct fields: trailing `/*< ... */`. No decorative dividers. |
| 3 | **Include order §5** | Own public header → other project headers → internal headers → third-party → stdlib. Blank line between groups. |
| 4 | **Types §8** | Fixed-width (`uint32_t` etc.) for struct fields and data. `size_t` for sizes. `int` only for returns/loops/flags. `PRIu64`/`%zu` for printf. |
| 5 | **Formatting §13** | Braces on ALL `if`/`else`/`for`/`while` bodies. `*` attaches to type (`int* p`). K&R brace style. One param per line when they don't fit. |
| 6 | **Extern §4** | Every non-static function declaration in `.h` files MUST have `extern`. |
| 7 | **Memory §16** | `calloc(1, sizeof(T))` with explicit cast. NULL check after alloc. NULL-safe destroy. Idempotent close with `closing` flag. |
| 8 | **Lifecycle §10** | Caller owns memory → `init`/`deinit`. Module owns memory → `create`/`destroy`. Never mix. |
| 9 | **Restricted §18** | No `sprintf`, `strcpy`, `strcat`, `gets`, `atoi`, `atof`, `atol`, `strtok`, `strerror`, `localtime`, `gmtime`. |
| 10 | **Opaque Structs §9** | Header: only `typedef struct <project>_foo_s <project>_foo_t;`. Full struct definition in `.c` only. Users never `sizeof()` — must use `create()`. Intrusive DS exempt. |
| 11 | **File Organization §11** | Order in `.c`: license → includes → macros → internal types → static vars → static functions (callees before callers, no forward decls) → public functions. |
| 12 | **Header guard §3** | `_Pragma("once")` only. No `#ifndef`/`#define` guards. |
| 13 | **Unused params §15** | `(void)param;` at top of function body. |
| 14 | **Platform §12** | No `#ifdef _WIN32` / `#ifdef __linux__` outside `src/platform/`. |

