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

> This checklist is a fast-scan subset covering the rules most often violated when editing code. It is NOT a substitute for `references/style.md`, which remains the complete and authoritative source. Passing the checklist does not by itself mean the code is fully compliant — when in doubt, consult the corresponding section in `style.md`.

### Checklist (ordered by frequency of violation)

| # | Rule | What to check |
|---|------|---------------|
| 1 | **Naming §7** | Public: `<project>_<module>_<action>`. Static: `_<module>_<action>`. Callbacks: `_<module>_<subject>_<event>_cb`. Types: `_t` suffix. Enums: `_e` tag, `_t` typedef, `UPPER` values. |
| 2 | **Comments §14** | ASCII only (no `//`, no unicode). Single-line `/* why */`; multi-line `/** ... */` (delimiters on own lines). Doxygen `/** @brief */` ONLY on function declarations — not types, typedefs, enums, structs, macros. Struct/enum fields: short → trailing `/* */`, long → `/** */` above. Explain only WHY; delete comments that restate code. No decorative dividers. |
| 3 | **Include order §5** | Own public header → other project headers → internal headers → third-party → stdlib. Blank line between groups. |
| 4 | **Types §8** | Fixed-width (`uint32_t` etc.) for fields/data, `size_t` for sizes, `int` only for returns/loops/flags. `PRIu64`/`%zu` for printf. |
| 5 | **Formatting §13** | Braces on ALL `if`/`else`/`for`/`while` bodies. `*` attaches to type (`int* p`). K&R braces. One param per line when they don't fit. |
| 6 | **Extern §4** | Every non-static function declaration in `.h` MUST have `extern`. |
| 7 | **Memory §16** | `calloc(1, sizeof(T))` with explicit cast. NULL check after alloc. NULL-safe destroy. Idempotent close via `closing` flag. |
| 8 | **Lifecycle §10** | Caller owns → `init`/`deinit`. Module owns → `create`/`destroy`. Never mix. |
| 9 | **Restricted §18** | No `sprintf`, `strcpy`, `strcat`, `gets`, `atoi`, `atof`, `atol`, `strtok`, `strerror`, `localtime`, `gmtime`. |
| 10 | **Opaque Structs §9** | Header: only `typedef struct <project>_foo_s <project>_foo_t;`. Full definition in `.c`. Users use `create()`, never `sizeof()`. Intrusive DS exempt. |
| 11 | **File Organization §11** | `.c` order: license → includes → macros → internal types → static vars → static functions (callees before callers, no forward decls) → public functions. |
| 12 | **Header guard §3** | `_Pragma("once")` only. No `#ifndef`/`#define` guards. |
| 13 | **Unused params §15** | `(void)param;` at top of function body. |
| 14 | **Platform §12** | No `#ifdef _WIN32` / `#ifdef __linux__` outside `src/platform/`. |
| 15 | **Logging §17.2** | Errors only via `<project>_loge`. No self-initiated `logd`/`logi`/`logw`. Message starts with module identifier, short and factual. Remove temporary debug logs. |
| 16 | **License Header §1** | Every `.c`/`.h` starts with the `LICENSE` text as `/** ... */`: opening `/**` first line, continuation ` *  `, closing ` */` own line. Easy to forget on new files. |
| 17 | **Return Conventions §17.1** | `int` → `0`/`-1`. Pointer → non-NULL/`NULL`. `ssize_t` → `>= 0`/`-1`. |
| 18 | **File Naming §6** | `<project>-` prefix = public. Public: `<project>-<module>[-<sub>].{c,h}`. Internal: `<module>-<name>.{c,h}`. Platform: `unix|win/platform-<module>.c`. Tests: `test-<module>.c`. Examples: `<topic>[-<pattern>]-<role>.c`. |
| 19 | **Test Code §21** | `#include "assert.h"` (not `<assert.h>`). One concern per `test_*`. Clean up every resource on every path. No shared file-scope state. No `sleep()`. Register via `<project>_add_test(<module>)`. |

