---
name: c-project-init
description: >
  Use when creating a new C project from scratch, or when asked to scaffold,
  init, or bootstrap a C library or application project with CMake. Also use
  when the user says "new project", "start a project", or needs a complete
  CMake + test + platform-layer skeleton generated.
---

# C Project Init

## When NOT to Use

building → c-project-build, writing code → c-project-style, committing → c-project-commit

## STOP — Read Reference Before Generating ANY Files

Read `references/setup.md` in this skill's base directory. If not found, STOP and tell the user.

Collect ALL inputs listed in `setup.md`'s Inputs table before generating anything. Do NOT assume defaults.

## Mandatory Post-Generation Verification

After generating project files, you MUST verify the following. Do NOT report done until all items pass.

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **No placeholders** | Grep all generated files for `{name}`, `{NAME}`, `{year}`, `{author}`, `{email}`, `{description}`, `{LICENSE_HEADER}`. Zero matches allowed (excluding cmake `${...}` expansions). |
| 2 | **File tree complete** | Every file listed in setup.md's File Tree section exists. No missing files. |
| 3 | **License header** | Every `.c` and `.h` file starts with the `/** Copyright ... */` block. |
| 4 | **Configures successfully** | Run `cmake -B out -G "Ninja Multi-Config"` — must return 0. |
| 5 | **Builds successfully** | Run `cmake --build out --config Debug` — must return 0. |
| 6 | **Style compliance** | All generated `.c`/`.h` files pass the c-project-style checklist. |
| 7 | **Platform mode correct** | If `windows`/`unix` mode: no `src/platform/` directory. If `cross-platform`: `platform.h` + `unix/.gitkeep` + `win/.gitkeep` all exist. |
