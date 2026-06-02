# Build Workflow

## Overview

Reference guide for the build/test/coverage cycle of C (C11+) CMake projects. All commands assume the project root contains a `CMakeLists.txt` with a valid `project()` call.

Placeholders:
- `{name}` -- lowercase project name from `CMakeLists.txt`
- `{NAME}` -- uppercase form
- `{build_dir}` -- CMake build directory (default: `out`). Detect from existing `cmake -B` invocations or `CMakeCache.txt` location. All commands below use `out` as the default; substitute the actual directory if different.

## Inputs — MANDATORY Checks Before Build

**STOP. Do NOT run any cmake command until you have collected ALL required inputs.**

| Input | How to obtain | Default |
|-------|---------------|---------|
| Project name | Read `project(...)` from root `CMakeLists.txt` | (required) |
| Build type | **Ask user**: Debug / Release / RelWithDebInfo / MinSizeRel | **(required, must ask)** |
| Feature flags | **Ask user** which optional features to enable | None |

Feature flags are project-specific `option()` entries in `CMakeLists.txt` (e.g. `{NAME}_ENABLE_TLS`). Scan the root `CMakeLists.txt` for all `option(...)` lines and present them to the user. Only enable flags the user explicitly requests.

Sanitizer and coverage are **not** part of the standard checks. Only ask about them when the user explicitly mentions sanitizer, ASAN, TSAN, UBSAN, or coverage in their request.

**An existing `out/` directory is NOT a reason to skip asking.** The cached config may be stale or wrong. Always confirm with the user before configuring or building.

**Red flags — if you catch yourself doing any of these, STOP:**
- "out/ exists, I'll just build" → STOP. Ask the user first.
- "It was Debug last time, probably still Debug" → STOP. Confirm.
- "I'll enable TLS because it was on before" → STOP. Ask.
- "User said compile, they just want a quick build" → STOP. Quick ≠ skip confirmation.

**Exception:** These checks do NOT apply during iterative fix cycles (rebuild-only, re-run tests, or fix→rebuild→test loops). See the skip-confirmation rules in SKILL.md.

## Build Type

| Build type | `--config` value | Use case |
|------------|--------------------|----------|
| Debug | `Debug` | Development, testing, sanitizers, coverage |
| Release | `Release` | Speed optimization (`-O2` / `/O2`) |
| RelWithDebInfo | `RelWithDebInfo` | Speed optimization + debug info |
| MinSizeRel | `MinSizeRel` | Size optimization (`-Os` / `/O1`) |

## Platform Strategy

All platforms use Ninja Multi-Config. Build type is selected at build time via `--config {build_type}`, not at configure time. This ensures `CMAKE_EXPORT_COMPILE_COMMANDS` produces `compile_commands.json`. Visual Studio generators do not produce this file.

### Windows MSVC Environment Activation

On Windows, Ninja and MSVC compiler require the Visual Studio developer environment.

**Step 1 — Locate `vcvarsall.bat`:**

Run `vswhere.exe` to find the VS installation path:

```
"{ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -property installationPath
```

The `vcvarsall.bat` is at: `{installationPath}\VC\Auxiliary\Build\vcvarsall.bat`

If `vswhere.exe` is not found, tell the user to install Visual Studio Build Tools.

**Step 2 — Generate `out/vcenv.cmd` wrapper (one-time):**

Create the file `out/vcenv.cmd` with this content (substitute the actual vcvarsall path):

```bat
@echo off
call "{vcvarsall}" x64 >nul 2>&1
%*
```

Example:

```bat
@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul 2>&1
%*
```

Generate this file once per configure. The `out/` directory must exist first (create it if needed before writing).

**Step 3 — Run all cmake/ctest commands through the wrapper:**

All Windows cmake/ctest commands in this document MUST be executed via `out/vcenv.cmd`:

| Shell | Pattern |
|-------|---------|
| bash | `cmd //c "out\\vcenv.cmd {cmake_command}"` |
| PowerShell | `& cmd /c "out\vcenv.cmd {cmake_command}"` |
| cmd | `out\vcenv.cmd {cmake_command}` |

Example (bash):
```bash
cmd //c "out\\vcenv.cmd cmake -B out -G \"Ninja Multi-Config\" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
```

Example (PowerShell):
```powershell
& cmd /c "out\vcenv.cmd cmake -B out -G `"Ninja Multi-Config`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
```

The exit code comes directly from cmake/ctest — no spurious -1 issue.

**Step 4 — Force the MSVC compiler explicitly:**

Activating the VS environment puts `cl.exe` on PATH, but it does NOT make CMake prefer it. With the Ninja generator, CMake scans PATH and may pick up gcc/clang (e.g. MinGW, LLVM, MSYS2) *before* `cl.exe`. The result: a build that silently uses the wrong compiler.

To guarantee MSVC, **always** pass the compiler explicitly on the configure line:

```
-DCMAKE_C_COMPILER=cl
```

This must be present on every Windows `cmake -B` (configure) command — standard build, sanitizers, and coverage. Without it, the only thing controlling compiler choice is PATH ordering, which is unreliable.

## compile_commands.json

After every successful configure or build, copy `compile_commands.json` from the build directory to the project root so clangd can find it:

| Platform | Command |
|----------|---------|
| Unix | `cp -f out/compile_commands.json compile_commands.json 2>/dev/null \|\| true` |
| Windows (bash) | `cp -f out/compile_commands.json compile_commands.json 2>/dev/null \|\| true` |
| Windows (PowerShell) | `Copy-Item -Force out\compile_commands.json compile_commands.json -ErrorAction SilentlyContinue` |

This file should be in `.gitignore`.

## Commands

### Configure

**MANDATORY: Always delete `out/` before configuring.** Stale cache can produce incorrect builds.

```bash
rm -rf out   # Unix / Windows (bash)
```
```powershell
if (Test-Path out) { Remove-Item -Recurse -Force out }   # Windows (PowerShell)
```

#### Unix (Linux / macOS)

```bash
cmake -B out -G "Ninja Multi-Config" \
  [-D{NAME}_ENABLE_TESTING=ON] \
  [-D{NAME}_ENABLE_{FEATURE}=ON]
```

#### Windows (MSVC + Ninja Multi-Config)

Use `out/vcenv.cmd` as described in **Windows MSVC Environment Activation**:

```bash
# bash
cmd //c "out\\vcenv.cmd cmake -B out -G \"Ninja Multi-Config\" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl [-D{NAME}_ENABLE_TESTING=ON] [-D{NAME}_ENABLE_{FEATURE}=ON]"
```
```powershell
# PowerShell
& cmd /c "out\vcenv.cmd cmake -B out -G `"Ninja Multi-Config`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl [-D{NAME}_ENABLE_TESTING=ON] [-D{NAME}_ENABLE_{FEATURE}=ON]"
```

### Build

Unix:

```bash
cmake --build out --config {build_type} -j {ncpu}
```

On Unix with Release/RelWithDebInfo/MinSizeRel, strip debug symbols after build:

```bash
strip out/{build_type}/{target}      # shared lib / executable
strip -g out/{build_type}/lib{name}.a  # static lib: strip debug only, keep symbols
```

Windows (via `out/vcenv.cmd`):

```bash
# bash
cmd //c "out\\vcenv.cmd cmake --build out --config {build_type} -j {ncpu}"
```
```powershell
# PowerShell
& cmd /c "out\vcenv.cmd cmake --build out --config {build_type} -j {ncpu}"
```

Detect CPU count:
- Linux: `nproc`
- macOS: `sysctl -n hw.ncpu`
- Windows: `%NUMBER_OF_PROCESSORS%` or default `8`
- Fallback: `4`

### Test

Unix:

```bash
ctest --test-dir out -C {build_type} --output-on-failure
```

Windows (via `out/vcenv.cmd`):

```bash
# bash
cmd //c "out\\vcenv.cmd ctest --test-dir out -C {build_type} --output-on-failure"
```
```powershell
# PowerShell
& cmd /c "out\vcenv.cmd ctest --test-dir out -C {build_type} --output-on-failure"
```

Run a single test module (add `-R {module}`):

```bash
ctest --test-dir out -C {build_type} -R {module} --output-on-failure        # Unix
```
```bash
# Windows (bash)
cmd //c "out\\vcenv.cmd ctest --test-dir out -C {build_type} -R {module} --output-on-failure"
```
```powershell
# Windows (PowerShell)
& cmd /c "out\vcenv.cmd ctest --test-dir out -C {build_type} -R {module} --output-on-failure"
```

### Sanitizers

Enable one sanitizer at a time. ASAN and TSAN cannot coexist.

Unix:

```bash
cmake -B out -G "Ninja Multi-Config" \
  -D{NAME}_ENABLE_TESTING=ON \
  -D{NAME}_ENABLE_ASAN=ON

cmake --build out --config Debug -j {ncpu}
ctest --test-dir out -C Debug --output-on-failure
```

Windows (via `out/vcenv.cmd`):

```bash
# bash
cmd //c "out\\vcenv.cmd cmake -B out -G \"Ninja Multi-Config\" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl -D{NAME}_ENABLE_TESTING=ON -D{NAME}_ENABLE_ASAN=ON"
cmd //c "out\\vcenv.cmd cmake --build out --config Debug -j {ncpu}"
cmd //c "out\\vcenv.cmd ctest --test-dir out -C Debug --output-on-failure"
```
```powershell
# PowerShell
& cmd /c "out\vcenv.cmd cmake -B out -G `"Ninja Multi-Config`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl -D{NAME}_ENABLE_TESTING=ON -D{NAME}_ENABLE_ASAN=ON"
& cmd /c "out\vcenv.cmd cmake --build out --config Debug -j {ncpu}"
& cmd /c "out\vcenv.cmd ctest --test-dir out -C Debug --output-on-failure"
```

| Sanitizer | Option | Catches |
|-----------|--------|---------|
| ASAN | `-D{NAME}_ENABLE_ASAN=ON` | Buffer overflow, use-after-free, memory leaks |
| TSAN | `-D{NAME}_ENABLE_TSAN=ON` | Data races, deadlocks |
| UBSAN | `-D{NAME}_ENABLE_UBSAN=ON` | Undefined behavior (signed overflow, null deref, etc.) |

UBSAN can be combined with ASAN or TSAN.

### Coverage

#### Unix

```bash
cmake -B out -G "Ninja Multi-Config" \
  -D{NAME}_ENABLE_TESTING=ON \
  -D{NAME}_ENABLE_COVERAGE=ON

cmake --build out --config Debug -j {ncpu}
cmake --build out --config Debug --target coverage
```

Requires `lcov` and `genhtml`. HTML report at `out/coverage/html/index.html`.

#### Windows

Windows coverage uses OpenCppCoverage (runtime instrumentation, no compiler flags needed). The `{NAME}_ENABLE_COVERAGE=ON` flag is needed so CMake creates the `coverage` target.

```bash
# bash
cmd //c "out\\vcenv.cmd cmake -B out -G \"Ninja Multi-Config\" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl -D{NAME}_ENABLE_TESTING=ON -D{NAME}_ENABLE_COVERAGE=ON"
cmd //c "out\\vcenv.cmd cmake --build out --config Debug -j 8"
cmd //c "out\\vcenv.cmd cmake --build out --config Debug --target coverage"
```
```powershell
# PowerShell
& cmd /c "out\vcenv.cmd cmake -B out -G `"Ninja Multi-Config`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=cl -D{NAME}_ENABLE_TESTING=ON -D{NAME}_ENABLE_COVERAGE=ON"
& cmd /c "out\vcenv.cmd cmake --build out --config Debug -j 8"
& cmd /c "out\vcenv.cmd cmake --build out --config Debug --target coverage"
```

HTML report at `out/coverage/index.html`.

If `cmake --build out --target coverage` fails with "no rule to make target 'coverage'", OpenCppCoverage is not installed or not on PATH. Install from https://github.com/OpenCppCoverage/OpenCppCoverage/releases, ensure on PATH, then reconfigure. Also check `tests/CMakeLists.txt` for the Windows coverage target — it may not be in the root CMakeLists.

## Reconfigure vs Rebuild

| Scenario | Action |
|----------|--------|
| Changed source files only | Build only (cmake --build out) |
| Any other change (options, CMakeLists.txt, sanitizer) | Delete `out/` and reconfigure from scratch |

**Rule: Every configure = delete `out/` first.** This prevents stale cache from producing incorrect builds.

Delete `out/` (see Configure section), then configure + build.

