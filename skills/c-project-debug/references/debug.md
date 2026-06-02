# Debug Workflow

## Overview

Non-interactive debugging for C (C11+) CMake projects. Three-tier strategy applied on all platforms:

1. **Sanitizer rebuild** — always try first, best diagnostics
2. **Batch-mode debugger** — when sanitizer output isn't enough
3. **Log-based debugging** — fallback when no debugger is installed

All commands assume the project is built in Debug mode (`--config Debug` with Ninja Multi-Config) with test binaries at `out/Debug/test-{module}` (Windows) or `out/Debug/test-{module}` (Unix).

Placeholders:
- `{name}` — lowercase project name from `CMakeLists.txt`
- `{NAME}` — uppercase form
- `{module}` — test module name (e.g. `tcp`, `list`, `udp`)

All commands below use `out` as the default build directory; substitute the actual directory if different.

## Prerequisites

The project MUST be built in Debug mode before debugging. Debug mode ensures:
- Debug symbols (`-g` / `/Zi`) are present for source-level backtraces
- No optimization (`-O0` / `/Od`) so variables aren't optimized away
- Frame pointers preserved for accurate stack unwinding

If `out/` was built with Release or another type, you MUST reconfigure and rebuild in Debug. Use the c-project-build skill for this.

## Step 0: Reproduce and Identify the Failing Test

**Always start here.** Before any debugger or sanitizer, identify WHICH test function fails:

```bash
ctest --test-dir out -C Debug -R {module} --output-on-failure
```

The project's `ASSERT` macro calls `abort()` on failure, printing `Test failed at {file}:{line}` to stderr before aborting. This output alone often pinpoints the exact assertion and line number.

If the test segfaults without hitting an ASSERT, ctest will show the signal. Either way, note:
- Which test function was running (the last `printf` or the abort message)
- The signal: SIGSEGV (null/bad pointer), SIGABRT (assertion/abort), SIGBUS (alignment)

**Binary paths:** With Ninja Multi-Config, test binaries are at `out/Debug/test-{module}` (or `out\Debug\test-{module}.exe` on Windows).

## Step 1: Sanitizer Rebuild (All Platforms — Always Try First)

Sanitizers instrument the binary at compile time and produce detailed diagnostics at runtime. They catch bugs that debugger backtraces miss (use-after-free, buffer overflow, undefined behavior).

**This is the most effective approach on ALL platforms.** Always try sanitizers before reaching for a debugger.

### ASAN + UBSAN (recommended combo)

Delete `out/` and reconfigure. Follow the **Sanitizers** section in c-project-build's `build.md` for the full configure/build/test flow. The key flags are:

- `-D{NAME}_ENABLE_TESTING=ON`
- `-D{NAME}_ENABLE_ASAN=ON`
- `-D{NAME}_ENABLE_UBSAN=ON` (Unix only — MSVC does not support UBSAN)

Quick reference (Unix):

```bash
rm -rf out
cmake -B out -G "Ninja Multi-Config" \
  -D{NAME}_ENABLE_TESTING=ON \
  -D{NAME}_ENABLE_ASAN=ON \
  -D{NAME}_ENABLE_UBSAN=ON
cmake --build out --config Debug -j $(nproc)
ctest --test-dir out -C Debug -R {module} --output-on-failure
```

On Windows, use the `out/vcenv.cmd` wrapper described in c-project-build's `build.md` (Windows MSVC Environment Activation section). MSVC supports ASAN only.

### What sanitizers catch

| Sanitizer | Option | Catches | Windows |
|-----------|--------|---------|---------|
| ASAN | `-D{NAME}_ENABLE_ASAN=ON` | Buffer overflow, use-after-free, double-free, memory leaks | ✅ |
| UBSAN | `-D{NAME}_ENABLE_UBSAN=ON` | Null deref, signed overflow, misaligned access | ❌ |
| TSAN | `-D{NAME}_ENABLE_TSAN=ON` | Data races, deadlocks | ❌ |

**ASAN and TSAN cannot coexist.** Choose one per build. UBSAN can combine with ASAN.

### Interpreting sanitizer output

ASAN output includes a symbolized stack trace with source locations. Look for:
- `ERROR: AddressSanitizer: heap-buffer-overflow` — writing past allocation
- `ERROR: AddressSanitizer: heap-use-after-free` — accessing freed memory
- `ERROR: AddressSanitizer: stack-buffer-overflow` — writing past stack array
- `SUMMARY: UndefinedBehaviorSanitizer` — UB with exact file:line

If sanitizer output clearly identifies the bug, skip to Step 3 (Analyze and Fix). If you need more context (e.g. variable values at crash time), proceed to Step 2.

## Step 2: Batch-Mode Debugger

Use when sanitizer output isn't sufficient — e.g. you know WHERE the crash is but need to inspect variable state, or the bug doesn't reproduce under sanitizers.

### Platform debugger selection

| Platform | Debugger | Check installed |
|----------|----------|-----------------|
| Windows | `cdb` (WinDbg command-line) | `where cdb` |
| Linux | `gdb` | `which gdb` |
| macOS | `lldb` | `which lldb` |

**If the debugger is not installed, guide the user to install it:**

- **cdb (Windows):** Install "Debugging Tools for Windows" from the Windows SDK. Download from https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/ — during installation, select only "Debugging Tools for Windows". After install, locate `cdb.exe` with `where cdb` or `dir /s /b "C:\Program Files (x86)\Windows Kits" cdb.exe`. Add to PATH or use full path.
- **gdb (Linux):** `sudo apt install gdb` (Debian/Ubuntu) or `sudo dnf install gdb` (Fedora/RHEL) or `sudo pacman -S gdb` (Arch)
- **lldb (macOS):** `xcode-select --install` (comes with Xcode Command Line Tools)

**If the user cannot or does not want to install a debugger, skip to Step 2F (Log-Based Debugging).**

### 2A. CDB — Windows batch backtrace

#### Basic backtrace

```bat
cdb -g -G -c "kb;q" out\Debug\test-{module}.exe
```

- `-g` — ignore initial breakpoint (run immediately)
- `-G` — ignore final breakpoint
- `kb` — display stack backtrace with parameters
- `q` — quit

#### With local variables

```bat
cdb -g -G -c "kP;q" out\Debug\test-{module}.exe
```

- `kP` — backtrace with full parameter and local variable values

#### Inspect specific variable at breakpoint

```bat
cdb -g -G -c "bp {module}!{function_name};g;dv;kb;q" out\Debug\test-{module}.exe
```

- `bp` — set breakpoint
- `g` — go (continue execution)
- `dv` — display local variables
- `kb` — backtrace

#### Analyze crash automatically

```bat
cdb -g -G -c "!analyze -v;q" out\Debug\test-{module}.exe
```

- `!analyze -v` — automatic crash analysis with verbose output (best single command for crash diagnosis)

### 2B. GDB — Linux batch backtrace

#### Basic backtrace

```bash
gdb -batch -ex run -ex "bt full" out/Debug/test-{module}
```

- `run` — starts the program; GDB stops on crash signal
- `bt full` — prints backtrace with local variable values in every frame

#### With registers and faulting instruction

```bash
gdb -batch -ex run -ex "info registers" -ex "x/i \$pc" -ex "bt full" out/Debug/test-{module}
```

- `info registers` — shows which register held the bad address
- `x/i $pc` — disassembles the faulting instruction

#### Inspect at breakpoint

```bash
gdb -batch \
  -ex "break {function_name}" \
  -ex run \
  -ex "print *{pointer}" \
  -ex "print {variable}" \
  -ex continue \
  -ex "bt full" \
  out/Debug/test-{module}
```

#### Watchpoint (catch when a value changes)

```bash
gdb -batch \
  -ex "break {function_name}" \
  -ex run \
  -ex "watch {variable}" \
  -ex continue \
  -ex "bt full" \
  out/Debug/test-{module}
```

#### Pass arguments

```bash
gdb -batch -ex run --args out/Debug/test-{module} arg1 arg2
```

### 2C. LLDB — macOS batch backtrace

#### Basic backtrace

```bash
lldb -b -o run -o "bt all" out/Debug/test-{module}
```

- `-b` — batch mode
- `-o` — execute command after loading

#### With local variables

```bash
lldb -b -o run -o "bt all" -o "frame variable" out/Debug/test-{module}
```

#### Inspect at breakpoint

```bash
lldb -b \
  -o "breakpoint set -n {function_name}" \
  -o run \
  -o "frame variable" \
  -o continue \
  -o "bt all" \
  out/Debug/test-{module}
```

### 2D. Interpreting backtraces

1. Find the topmost frame in YOUR source code (skip libc/system/CRT frames)
2. Note the file, line number, and function name
3. Check local variable values — look for NULL pointers, garbage values, or suspiciously large numbers
4. For intrusive data structures: check `prev`/`next` pointers for NULL or self-referential loops

### 2E. Debugging Hangs

If a test hangs instead of crashing:

#### Unix: attach to running process

```bash
out/Debug/test-{module} &
PID=$!
sleep 5
gdb -batch -ex "thread apply all bt full" -p $PID
kill $PID
```

Or with lldb on macOS:

```bash
out/Debug/test-{module} &
PID=$!
sleep 5
lldb -b -o "bt all" -p $PID
kill $PID
```

#### Windows: attach with cdb

```bat
start /B out\Debug\test-{module}.exe
timeout /t 5 >nul
:: Find PID with tasklist, then:
cdb -p {PID} -c "~*kb;q"
taskkill /F /PID {PID}
```

#### Alternative (Unix): timeout + core dump

```bash
ulimit -c unlimited
timeout 10 out/Debug/test-{module}
gdb -batch -ex "bt full" out/Debug/test-{module} core
```

#### Common hang causes in event-loop code

- Safety timer not set (test runs forever waiting for callback that never fires)
- `<project>_loop_stop` never called (missing callback, wrong condition)
- Deadlock in thread pool or waitgroup
- Socket not closed (event loop keeps running)

### 2F. Log-Based Debugging (Fallback)

**Use when no debugger is installed and the user cannot install one.**

Add `fprintf(stderr, ...)` calls at key points to narrow down the crash location. This requires recompilation after each change.

#### Strategy: binary search with logs

1. Identify the failing test function from Step 0
2. Add a log at the midpoint of the function:

```c
fprintf(stderr, "DEBUG: reached checkpoint A\n");
```

3. Rebuild and run:

```bash
cmake --build out -j {ncpu}
ctest --test-dir out -C Debug -R {module} --output-on-failure
```

4. If "checkpoint A" prints → crash is AFTER that point. Move log forward.
5. If "checkpoint A" doesn't print → crash is BEFORE that point. Move log backward.
6. Repeat until you've narrowed to 2-3 lines.

#### Printing variable values

```c
fprintf(stderr, "DEBUG: ptr=%p, len=%zu, state=%d\n",
        (void*)ptr, len, state);
```

#### Printing pointer chain (intrusive data structures)

```c
fprintf(stderr, "DEBUG: node=%p, node->prev=%p, node->next=%p\n",
        (void*)node, (void*)node->prev, (void*)node->next);
```

#### Important rules for log debugging

- Always use `stderr` (not `stdout`) — stderr is unbuffered, so logs appear even if the program crashes immediately after
- Always rebuild after adding/removing logs — C requires recompilation
- Remove all debug logs after fixing the bug — do NOT commit them
- Use a consistent prefix like `DEBUG:` so logs are easy to grep and remove

## Step 3: Analyze and Fix

After collecting diagnostic output (sanitizer report, backtrace, or logs):

1. **Read the source** at the crash location — understand what the code expected vs what happened
2. **Trace the data flow** — how did the bad pointer/value get there? Follow it backwards through callers
3. **Check the test setup** — is the test correctly initializing structures? Missing `init()` calls?
4. **Look for common C bugs:**
   - Use-after-free: pointer to stack variable that went out of scope
   - Double-free: resource freed twice in cleanup path
   - NULL dereference: missing NULL check on return value
   - Buffer overflow: writing past array bounds
   - Uninitialized memory: struct field not zeroed before use
   - Off-by-one: loop bounds, array indexing

5. **Fix and verify** — after fixing, rebuild and run the test again. Then run with ASAN to confirm no latent issues.

## Decision Guide

```
Test failing?
├── Step 0: ctest --output-on-failure (identify which test)
├── Step 1: Sanitizer rebuild (ASAN, always try first)
│   ├── Sanitizer identifies bug → Step 3 (fix)
│   └── Need more context → Step 2
├── Step 2: Batch debugger
│   ├── Debugger installed → use cdb/gdb/lldb
│   ├── Not installed → guide user to install
│   └── Cannot install → Step 2F (log-based debugging)
└── Hang (timeout)
    └── Step 2E (attach to process)
```
