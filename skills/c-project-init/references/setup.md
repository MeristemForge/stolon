# Project Setup

## Contents

1. [Prerequisites](#prerequisites)
2. [Inputs](#inputs)
3. [File Tree](#file-tree)
4. [File Contents](#file-contents)
   - [LICENSE](#license)
   - [License Header Block](#license-header-block)
   - [AUTHORS](#authors)
   - [.clang-format](#clang-format)
   - [.gitignore](#gitignore)
   - [README.md](#readmemd)
   - [cmake/{name}-utils.cmake](#cmakename-utilscmake)
   - [docs/build.md](#docsbuildmd)
   - [tests/assert.h](#testsasserth)
   - [tests/CMakeLists.txt](#testscmakeliststxt)
   - [include/{name}.h](#includenameh-library-only)
   - [examples/CMakeLists.txt](#examplescmakeliststxt-library-only)
   - [src/platform/](#srcplatformplatformh)
   - [CMakeLists.txt — Library](#cmakeliststxt--library)
   - [CMakeLists.txt — Application](#cmakeliststxt--application)
   - [src/main.c](#srcmainc-application-only)
5. [Verification](#verification)

## Prerequisites

If the project root already contains a `CMakeLists.txt` with a valid `project()` call (no `{...}` placeholders), this setup is already done. Do not run it again.

## Inputs

Ask the user for all required inputs before generating any files.

| Input | Example | Required |
|-------|---------|----------|
| Project name | `myapp` | Yes |
| Project type | `library` or `application` | Yes |
| Platform | `cross-platform`, `windows`, or `unix` | Yes (always ask) |
| Description | One-line summary | Yes |
| Author | `John Doe` | Yes |
| Email | `john@example.com` | Yes |
| Year | `2026` or `2026-2036` | No (default: current year) |

Derive two forms from the project name:
- `{name}` — lowercase (e.g. `myapp`)
- `{NAME}` — uppercase (e.g. `MYAPP`)

### Platform Modes

| Mode | Meaning |
|------|---------|
| `cross-platform` | Full Windows + Unix support. Platform layer has `unix/` and `win/` subdirectories. CMakeLists.txt has `if(WIN32)` / `if(UNIX)` branches. |
| `windows` | Windows only. No `src/platform/` directory. No `if(UNIX)` branches. |
| `unix` | Linux and macOS. No `src/platform/` directory. No `if(WIN32)` branches. |

## File Tree

All file trees below show the `cross-platform` layout. For single-platform modes, apply these adjustments:

| Adjustment | `windows` | `unix` |
|------------|-----------|--------|
| `src/platform/` | Omit entirely | Omit entirely |

### Library

```
{name}/
  .clang-format
  .gitignore
  AUTHORS
  LICENSE
  README.md
  CMakeLists.txt
  cmake/{name}-utils.cmake
  docs/build.md
  include/{name}.h                  (umbrella header)
  examples/CMakeLists.txt
  src/platform/platform.h
  src/platform/unix/.gitkeep
  src/platform/win/.gitkeep
  tests/assert.h
  tests/CMakeLists.txt
```

### Application

No `include/` directory. No `examples/` directory. Has `src/main.c`.

```
{name}/
  .clang-format
  .gitignore
  AUTHORS
  LICENSE
  README.md
  CMakeLists.txt
  cmake/{name}-utils.cmake
  docs/build.md
  src/main.c
  src/platform/platform.h
  src/platform/unix/.gitkeep
  src/platform/win/.gitkeep
  tests/assert.h
  tests/CMakeLists.txt
```


## File Contents

### LICENSE

MIT license. The `====` fences are part of the format.

```
MIT License

====
Copyright (c) {year}, {author} <{email}>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
====
```

### License Header Block

Every `.c` and `.h` file starts with the license text formatted as a `/** ... */` comment. The opening `/**` sits on the same line as the first word of the copyright. Each continuation line starts with ` *  ` (space-star-two-spaces). The closing ` */` is on its own line. Derive the content from the LICENSE file, stripping the `====` fences and the `MIT License` title line.

Example (for author `John Doe`, email `john@example.com`, year `2026`):

```c
/** Copyright (c) 2026, John Doe <john@example.com>
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the "Software"), to
 *  deal in the Software without restriction, including without limitation the
 *  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 *  sell copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in
 *  all copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 *  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 *  IN THE SOFTWARE.
 */
```

All `.c` and `.h` files below use `{LICENSE_HEADER}` as shorthand for this block.


### AUTHORS

```
# Authors (ordered by first contribution)

- {author} <{email}>
```

### .clang-format

```yaml
BasedOnStyle: LLVM
UseTab: Never
IndentWidth: 4
TabWidth: 4
PointerAlignment: Left
BinPackArguments: false
BinPackParameters: false
AlignConsecutiveDeclarations: true
AlignAfterOpenBracket: AlwaysBreak
AllowShortFunctionsOnASingleLine: None
```

### .gitignore

```
.vs/
out/
.cache/
compile_commands.json
.DS_Store
```


### README.md

Note: `\``` ` below is an escape for embedding code fences inside this document. When generating the actual file, output normal ` ``` ` (no backslash).

```markdown
# Overview

> {description}

# Features

<!-- Add project features here -->

# Build

\```bash
cmake -B out
cmake --build out
\```

See [docs/build.md](docs/build.md) for detailed instructions on generators, sanitizers, and coverage.

# Documentation

See the [docs/](docs/) directory for design documents and build instructions.

# License

\```
Copyright (c) {year}, {author} <{email}>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
\```
```


### cmake/{name}-utils.cmake

```cmake
function({name}_apply_sanitizer TARGET NAME FLAG)
    if(${NAME})
        if(WIN32 AND CMAKE_C_COMPILER_ID STREQUAL "MSVC")
            target_compile_options(${TARGET} PRIVATE "/fsanitize=${FLAG}")
            target_link_options(${TARGET} PRIVATE "/fsanitize=${FLAG}")
        elseif(UNIX)
            target_compile_options(${TARGET} PRIVATE "-fsanitize=${FLAG}" -fno-omit-frame-pointer)
            target_link_options(${TARGET} PUBLIC "-fsanitize=${FLAG}")
        endif()
    endif()
endfunction()

function({name}_add_test test_name)
    add_executable(test-${test_name} "test-${test_name}.c")
    target_link_libraries(test-${test_name} PRIVATE {name})
    add_test(NAME ${test_name} COMMAND test-${test_name})

    {name}_apply_sanitizer(test-${test_name} {NAME}_ENABLE_ASAN address)
    {name}_apply_sanitizer(test-${test_name} {NAME}_ENABLE_TSAN thread)
    {name}_apply_sanitizer(test-${test_name} {NAME}_ENABLE_UBSAN undefined)

    if({NAME}_ENABLE_COVERAGE AND UNIX)
        target_link_options(test-${test_name} PRIVATE --coverage)
    endif()
endfunction()
```

For application projects, change the `target_link_libraries` line inside `{name}_add_test` to link against `{name}_lib` instead of `{name}`, because `{name}` is the executable target and tests cannot link against an executable.


### docs/build.md

Note: `\``` ` below is an escape for embedding code fences inside this document. When generating the actual file, output normal ` ``` ` (no backslash).

```markdown
# Build Instructions

This guide covers building, testing, and generating coverage reports on Windows and Unix using CMake.

## Prerequisites

- CMake >= 3.25
- A C11-compatible compiler:
  - Windows: MSVC (Visual Studio 2022+) or Clang-cl
  - Linux/macOS: GCC >= 7 or Clang >= 6
- (Optional) For code coverage:
  - Linux: `lcov` and `genhtml` (`sudo apt install lcov`)
  - Windows: OpenCppCoverage (`winget install OpenCppCoverage.OpenCppCoverage`)

## Configure

### Multi-Config Generators (Visual Studio, Ninja Multi-Config)

\```bash
cmake -B out
\```

### Single-Config Generators (Unix Makefiles, Ninja)

\```bash
cmake -B out -DCMAKE_BUILD_TYPE=Debug
\```

## Build

### Multi-Config

\```bash
cmake --build out --config Debug -j 8
\```

### Single-Config

\```bash
cmake --build out -j 8
\```

## Run Tests

### Multi-Config

\```bash
ctest --test-dir out -C Debug --output-on-failure
\```

### Single-Config

\```bash
ctest --test-dir out --output-on-failure
\```

### Running a Single Test

\```bash
ctest --test-dir out -R <module> --output-on-failure
\```

## Sanitizers

\```bash
cmake -B out -D{NAME}_ENABLE_ASAN=ON
cmake --build out
\```

| Sanitizer | What it catches | Option | Windows |
|-----------|----------------|--------|---------|
| ASAN | Buffer overflow, use-after-free, memory leaks | `-D{NAME}_ENABLE_ASAN=ON` | Yes |
| TSAN | Data races, deadlocks | `-D{NAME}_ENABLE_TSAN=ON` | No |
| UBSAN | Undefined behavior | `-D{NAME}_ENABLE_UBSAN=ON` | No |

ASAN and TSAN cannot be enabled simultaneously.

### Windows ASAN Note

When running ASAN-instrumented binaries on Windows, always use a Developer Command Prompt (e.g., x64 Native Tools Command Prompt for VS 2022). This environment sets up the runtime paths for `clang_rt.asan_dynamic-x86_64.dll`. Running from a plain terminal will fail with a missing DLL error.

### TSAN on Linux

TSAN requires GCC 13+ / glibc 2.36+ to correctly intercept C11 `thrd_create`. On older toolchains, glibc's `thrd_create` calls `pthread_create` via an internal direct call that bypasses TSAN's interception.

When running under WSL, TSAN may report `FATAL: ThreadSanitizer: unexpected memory mapping` due to WSL's non-standard ASLR behavior. Use `setarch -R` to disable ASLR:

\```bash
setarch -R ctest --test-dir out --output-on-failure
\```

This is not needed on native Linux or macOS.

## Code Coverage

### Linux/macOS

\```bash
cmake -B out -D{NAME}_ENABLE_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build out -j 8
cmake --build out --target coverage
\```

### Windows

\```bash
cmake -B out -D{NAME}_ENABLE_COVERAGE=ON
cmake --build out --config Debug
cmake --build out --target coverage
\```

HTML report at `out/coverage/html/index.html`.

## Quick Reference

| Step | Multi-Config | Single-Config |
|------|-------------|---------------|
| Configure | No `-DCMAKE_BUILD_TYPE` | Must set `-DCMAKE_BUILD_TYPE=Debug` |
| Build | `--build ... --config Debug` | `--build ...` |
| Test | `ctest ... -C Debug` | `ctest ...` |
```


### tests/assert.h

```c
{LICENSE_HEADER}

_Pragma("once")

#include <stdio.h>
#include <stdlib.h>

#undef ASSERT
#define ASSERT(expr)                                                           \
    do {                                                                       \
        if (!(expr)) {                                                         \
            fprintf(stderr, "Test failed at %s:%d\n", __FILE__, __LINE__);     \
            abort();                                                           \
        }                                                                      \
    } while (0)
```

### tests/CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.25)

project(tests LANGUAGES C)

include({name}-utils)

# {name}_add_test(<module>)

if({NAME}_ENABLE_COVERAGE AND WIN32)
    find_program(OPENCPPCOVERAGE_BIN OpenCppCoverage)
    if(OPENCPPCOVERAGE_BIN)
        file(TO_NATIVE_PATH "${CMAKE_SOURCE_DIR}/src" SRC_DIR_NATIVE)
        file(TO_NATIVE_PATH "${CMAKE_SOURCE_DIR}/tests" TESTS_DIR_NATIVE)
        file(TO_NATIVE_PATH "${CMAKE_BINARY_DIR}/coverage" COVERAGE_OUTPUT_DIR_NATIVE)

        add_custom_target(coverage
            COMMAND ${OPENCPPCOVERAGE_BIN}
                "--sources=${SRC_DIR_NATIVE}"
                "--excluded_sources=${TESTS_DIR_NATIVE}"
                "--export_type=html:${COVERAGE_OUTPUT_DIR_NATIVE}"
                "--cover_children"
                "--"
                ctest.exe --test-dir "${CMAKE_BINARY_DIR}" -C $<CONFIG> --output-on-failure
            WORKING_DIRECTORY "${CMAKE_BINARY_DIR}"
            COMMENT "generating HTML coverage report in coverage/index.html"
            USES_TERMINAL
        )
    else()
        message(WARNING "OpenCppCoverage not found. install it and add to PATH.")
    endif()
endif()

if({NAME}_ENABLE_COVERAGE AND UNIX)
    find_program(LCOV_BIN lcov)
    find_program(GENHTML_BIN genhtml)
    if(LCOV_BIN AND GENHTML_BIN)
        add_custom_target(coverage
            COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/coverage
            COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/coverage
            COMMAND ctest --test-dir ${CMAKE_BINARY_DIR} -C $<CONFIG> --output-on-failure
            COMMAND ${LCOV_BIN} --capture --directory . --output-file ${CMAKE_BINARY_DIR}/coverage/coverage.info
            COMMAND ${GENHTML_BIN} ${CMAKE_BINARY_DIR}/coverage/coverage.info --output-directory ${CMAKE_BINARY_DIR}/coverage/html
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMENT "generating html coverage report in coverage/html/index.html"
        )
    else()
        message(WARNING "lcov or genhtml not found; 'coverage' target not created.")
    endif()
endif()
```

### include/{name}.h (library only)

```c
{LICENSE_HEADER}
_Pragma("once")

/* Include module headers below */
```

The `include/{name}/` subdirectory does not exist at project creation. It is created when the first module is added.

### examples/CMakeLists.txt (library only)

```cmake
cmake_minimum_required(VERSION 3.25)

project(examples LANGUAGES C)
```

### src/platform/platform.h

```c
{LICENSE_HEADER}

_Pragma("once")

/* Include platform-specific headers below */
```

### src/platform/unix/.gitkeep and src/platform/win/.gitkeep

Empty files. They ensure the directories exist in version control. Only generated for `cross-platform` mode.

### Platform Adjustments for Single-Platform Modes

When platform is `windows` or `unix`, apply these changes to the cross-platform templates above:

#### src/platform/

Omit the entire `src/platform/` directory (including `platform.h`, `unix/`, `win/`). The platform abstraction layer only exists for cross-platform projects. Single-platform code goes directly in `src/`.

#### CMakeLists.txt (both library and application)

| Cross-platform code | `windows` | `unix` |
|---------------------|-----------|--------|
| `if(WIN32) add_compile_options("/experimental:c11atomics") endif()` | Keep (unconditional, remove the `if`/`endif` wrapper) | Remove entirely |
| `if(WIN32) list(APPEND SRCS ...) endif()` | Keep (unconditional, remove the `if`/`endif` wrapper) | Remove entirely |
| `if(UNIX) list(APPEND SRCS ...) endif()` | Remove entirely | Keep (unconditional, remove the `if`/`endif` wrapper) |

#### cmake/{name}-utils.cmake

| Cross-platform code | `windows` | `unix` |
|---------------------|-----------|--------|
| `if(WIN32 AND CMAKE_C_COMPILER_ID STREQUAL "MSVC") ... elseif(UNIX) ... endif()` | Keep only the MSVC branch (unconditional) | Keep only the UNIX branch (unconditional) |

#### tests/CMakeLists.txt

| Cross-platform code | `windows` | `unix` |
|---------------------|-----------|--------|
| `if({NAME}_ENABLE_COVERAGE AND WIN32) ... endif()` | Keep (replace `AND WIN32` with just `{NAME}_ENABLE_COVERAGE`) | Remove entirely |
| `if({NAME}_ENABLE_COVERAGE AND UNIX) ... endif()` | Remove entirely | Keep (replace `AND UNIX` with just `{NAME}_ENABLE_COVERAGE`) |

#### .gitignore

| Cross-platform entry | `windows` | `unix` |
|----------------------|-----------|--------|
| `.vs/` | Keep | Remove |
| `.DS_Store` | Remove | Keep |


### CMakeLists.txt — Library

```cmake
cmake_minimum_required(VERSION 3.25)

project({name} LANGUAGES C)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include({name}-utils)

option({NAME}_ENABLE_TESTING "enable unit testing" OFF)
option({NAME}_ENABLE_ASAN "enable memory error detection" OFF)
option({NAME}_ENABLE_TSAN  "enable data race detection" OFF)
option({NAME}_ENABLE_UBSAN "enable undefined behavior detection" OFF)
option({NAME}_ENABLE_DYNAMIC_LIBRARY "build dynamic library" OFF)
option({NAME}_ENABLE_COVERAGE "enable code coverage reporting" OFF)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install")
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)
set(CMAKE_C_STANDARD 11)

if(WIN32)
	add_compile_options("/experimental:c11atomics")
endif()

set(SRCS
)

if(WIN32)
	list(APPEND SRCS
	)
endif()

if(UNIX)
	list(APPEND SRCS
	)
endif()

if({NAME}_ENABLE_DYNAMIC_LIBRARY)
    add_library({name} SHARED ${SRCS})
else()
    add_library({name} STATIC ${SRCS})
endif()

target_include_directories({name}
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries({name} PRIVATE ${CMAKE_DL_LIBS})

{name}_apply_sanitizer({name} {NAME}_ENABLE_ASAN address)
{name}_apply_sanitizer({name} {NAME}_ENABLE_TSAN thread)
{name}_apply_sanitizer({name} {NAME}_ENABLE_UBSAN undefined)

if({NAME}_ENABLE_COVERAGE AND UNIX)
    target_compile_options({name} PRIVATE --coverage)
    target_link_options({name} PUBLIC --coverage)
endif()

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include DESTINATION . FILES_MATCHING PATTERN "*")
install(TARGETS {name} DESTINATION lib)

add_subdirectory(examples)

if({NAME}_ENABLE_TESTING)
	enable_testing()
	add_subdirectory(tests)
endif()
```

### CMakeLists.txt — Application

Key differences from library: no `DYNAMIC_LIBRARY` option, no `include/` in target_include_directories, no `examples` subdirectory, uses `add_executable` + internal `{name}_lib` static library for testability.

```cmake
cmake_minimum_required(VERSION 3.25)

project({name} LANGUAGES C)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include({name}-utils)

option({NAME}_ENABLE_TESTING "enable unit testing" OFF)
option({NAME}_ENABLE_ASAN "enable memory error detection" OFF)
option({NAME}_ENABLE_TSAN  "enable data race detection" OFF)
option({NAME}_ENABLE_UBSAN "enable undefined behavior detection" OFF)
option({NAME}_ENABLE_COVERAGE "enable code coverage reporting" OFF)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)
set(CMAKE_C_STANDARD 11)

if(WIN32)
	add_compile_options("/experimental:c11atomics")
endif()

set(SRCS
)

if(WIN32)
	list(APPEND SRCS
	)
endif()

if(UNIX)
	list(APPEND SRCS
	)
endif()

add_library({name}_lib STATIC ${SRCS})

target_include_directories({name}_lib
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries({name}_lib PRIVATE ${CMAKE_DL_LIBS})

{name}_apply_sanitizer({name}_lib {NAME}_ENABLE_ASAN address)
{name}_apply_sanitizer({name}_lib {NAME}_ENABLE_TSAN thread)
{name}_apply_sanitizer({name}_lib {NAME}_ENABLE_UBSAN undefined)

if({NAME}_ENABLE_COVERAGE AND UNIX)
    target_compile_options({name}_lib PRIVATE --coverage)
    target_link_options({name}_lib PUBLIC --coverage)
endif()

add_executable({name} src/main.c)
target_link_libraries({name} PRIVATE {name}_lib)

{name}_apply_sanitizer({name} {NAME}_ENABLE_ASAN address)
{name}_apply_sanitizer({name} {NAME}_ENABLE_TSAN thread)
{name}_apply_sanitizer({name} {NAME}_ENABLE_UBSAN undefined)

install(TARGETS {name} DESTINATION bin)

if({NAME}_ENABLE_TESTING)
	enable_testing()
	add_subdirectory(tests)
endif()
```

### src/main.c (application only)

```c
{LICENSE_HEADER}

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;
    return 0;
}
```

## Verification

After generating all files, search every file for the regex `(?<!\$)\{(name|NAME|year|author|email|description|LICENSE_HEADER)\}` (case-insensitive). The negative lookbehind `(?<!\$)` excludes cmake variable expansions like `${NAME}`. No matches should remain.