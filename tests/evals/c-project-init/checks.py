"""Deterministic checks for c-project-init skill eval.

Each check function:
  - Named check_<name> matching the id in prompts.json expected_checks
  - Returns True (pass) or False (fail)
  - Has an 'input_type' attribute: "directory" for project dir, "text" for output text
"""

import re
from pathlib import Path


def directory_check(fn):
    fn.input_type = "directory"
    return fn


def text_check(fn):
    fn.input_type = "text"
    return fn


# --- Structure checks ---


@directory_check
def check_has_cmakelists(d: Path) -> bool:
    return (d / "CMakeLists.txt").exists()


@directory_check
def check_no_unreplaced_placeholders(d: Path) -> bool:
    # Match {name}, {NAME}, etc. but NOT ${NAME} (cmake variable expansion)
    pattern = re.compile(
        r"(?<!\$)\{(name|NAME|year|author|email|description|LICENSE_HEADER)\}", re.I
    )
    for f in d.rglob("*"):
        if f.is_file() and f.suffix in (".c", ".h", ".cmake", ".txt", ".md", ".sh", ".bat", ""):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if pattern.search(text):
                return False
    return True


@directory_check
def check_cmake_has_project_options(d: Path) -> bool:
    cm = d / "CMakeLists.txt"
    if not cm.exists():
        return False
    text = cm.read_text(encoding="utf-8")
    return all(
        opt in text
        for opt in ("ENABLE_TESTING", "ENABLE_ASAN", "ENABLE_TSAN", "ENABLE_UBSAN")
    )


@directory_check
def check_cmake_c_standard_11(d: Path) -> bool:
    cm = d / "CMakeLists.txt"
    return cm.exists() and "CMAKE_C_STANDARD 11" in cm.read_text(encoding="utf-8")


@directory_check
def check_cmake_version_325(d: Path) -> bool:
    cm = d / "CMakeLists.txt"
    return cm.exists() and "cmake_minimum_required(VERSION 3.25)" in cm.read_text(
        encoding="utf-8"
    )


@directory_check
def check_target_include_directories(d: Path) -> bool:
    cm = d / "CMakeLists.txt"
    if not cm.exists():
        return False
    text = cm.read_text(encoding="utf-8")
    has_target = "target_include_directories(" in text
    has_bare = bool(re.search(r"(?<!target_)include_directories\(", text))
    return has_target and not has_bare


@directory_check
def check_has_clang_format(d: Path) -> bool:
    return (d / ".clang-format").exists()


@directory_check
def check_has_gitignore(d: Path) -> bool:
    return (d / ".gitignore").exists()


@directory_check
def check_has_license_mit(d: Path) -> bool:
    lic = d / "LICENSE"
    return lic.exists() and "MIT" in lic.read_text(encoding="utf-8")


@directory_check
def check_has_license_fences(d: Path) -> bool:
    """LICENSE uses ==== fences (the scaffold format defined in setup.md)."""
    lic = d / "LICENSE"
    if not lic.exists():
        return False
    text = lic.read_text(encoding="utf-8")
    return text.count("====") >= 2


@directory_check
def check_cmake_utils_renamed(d: Path) -> bool:
    cmake_dir = d / "cmake"
    if not cmake_dir.is_dir():
        return False
    if (cmake_dir / "utils.cmake").exists():
        return False
    return any(cmake_dir.glob("*-utils.cmake"))


@directory_check
def check_has_platform_dir(d: Path) -> bool:
    p = d / "src" / "platform"
    return (
        p.is_dir()
        and (p / "platform.h").exists()
        and (p / "unix").is_dir()
        and (p / "win").is_dir()
    )


@directory_check
def check_has_assert_h(d: Path) -> bool:
    ah = d / "tests" / "assert.h"
    if not ah.exists():
        return False
    text = ah.read_text(encoding="utf-8")
    return "ASSERT" in text and "abort()" in text


@directory_check
def check_has_build_scripts(d: Path) -> bool:
    return (d / "build.sh").exists() and (d / "build.bat").exists()


@directory_check
def check_tests_cmake_has_coverage(d: Path) -> bool:
    tc = d / "tests" / "CMakeLists.txt"
    if not tc.exists():
        return False
    text = tc.read_text(encoding="utf-8")
    return "ENABLE_COVERAGE" in text and "coverage" in text


@directory_check
def check_license_header_in_c_files(d: Path) -> bool:
    """All .c and .h files (except .gitkeep) start with /** license header."""
    for f in d.rglob("*"):
        if f.is_file() and f.suffix in (".c", ".h") and f.name != ".gitkeep":
            text = f.read_text(encoding="utf-8", errors="ignore").lstrip()
            if not text.startswith("/**"):
                return False
    return True


@directory_check
def check_output_dir_is_out(d: Path) -> bool:
    """Build output directory convention is 'out'."""
    for name in ("build.sh", "build.bat", "docs/build.md"):
        f = d / name
        if f.exists() and "out" in f.read_text(encoding="utf-8", errors="ignore"):
            return True
    return False


@directory_check
def check_has_authors(d: Path) -> bool:
    return (d / "AUTHORS").exists()


# --- Library-specific checks ---


@directory_check
def check_lib_has_include_header(d: Path) -> bool:
    inc = d / "include"
    return inc.is_dir() and any(inc.glob("*.h"))


@directory_check
def check_lib_has_examples_dir(d: Path) -> bool:
    return (d / "examples").is_dir()


@directory_check
def check_lib_no_main_c(d: Path) -> bool:
    return not (d / "src" / "main.c").exists()


@directory_check
def check_lib_has_dynamic_library_option(d: Path) -> bool:
    cm = d / "CMakeLists.txt"
    return cm.exists() and "ENABLE_DYNAMIC_LIBRARY" in cm.read_text(encoding="utf-8")


# --- Application-specific checks ---


@directory_check
def check_app_has_main_c(d: Path) -> bool:
    return (d / "src" / "main.c").exists()


@directory_check
def check_app_no_include_dir(d: Path) -> bool:
    return not (d / "include").is_dir()


@directory_check
def check_app_no_examples_dir(d: Path) -> bool:
    return not (d / "examples").is_dir()


@directory_check
def check_app_has_lib_target(d: Path) -> bool:
    """Application CMakeLists.txt uses an internal _lib static library."""
    cm = d / "CMakeLists.txt"
    if not cm.exists():
        return False
    text = cm.read_text(encoding="utf-8")
    return "_lib STATIC" in text


@directory_check
def check_app_tests_link_lib(d: Path) -> bool:
    """Application utils.cmake links tests against _lib, not the executable."""
    cmake_dir = d / "cmake"
    if not cmake_dir.is_dir():
        return False
    for f in cmake_dir.glob("*-utils.cmake"):
        text = f.read_text(encoding="utf-8")
        if "_lib)" in text or "_lib )" in text:
            return True
    return False


# --- Negative check ---


@text_check
def check_no_c_skill_content(text: str) -> bool:
    return not bool(
        re.search(
            r"CMakeLists|cmake|sanitizer|ASAN|clang-format|\.c\b.*file", text, re.I
        )
    )


# --- Unix-only platform checks ---


@directory_check
def check_unix_has_build_sh(d: Path) -> bool:
    return (d / "build.sh").exists()


@directory_check
def check_unix_no_build_bat(d: Path) -> bool:
    return not (d / "build.bat").exists()


@directory_check
def check_unix_no_platform_dir(d: Path) -> bool:
    """Unix-only projects should not have src/platform/ at all."""
    return not (d / "src" / "platform").is_dir()


@directory_check
def check_unix_cmake_no_win32_branch(d: Path) -> bool:
    """CMakeLists.txt should not have if(WIN32) branches."""
    cm = d / "CMakeLists.txt"
    if not cm.exists():
        return False
    text = cm.read_text(encoding="utf-8")
    return "if(WIN32)" not in text


@directory_check
def check_unix_coverage_no_win32(d: Path) -> bool:
    """tests/CMakeLists.txt coverage section should not have WIN32."""
    tc = d / "tests" / "CMakeLists.txt"
    if not tc.exists():
        return False
    text = tc.read_text(encoding="utf-8")
    return "WIN32" not in text


# --- Windows-only platform checks ---


@directory_check
def check_win_has_build_bat(d: Path) -> bool:
    return (d / "build.bat").exists()


@directory_check
def check_win_no_build_sh(d: Path) -> bool:
    return not (d / "build.sh").exists()


@directory_check
def check_win_no_platform_dir(d: Path) -> bool:
    """Windows-only projects should not have src/platform/ at all."""
    return not (d / "src" / "platform").is_dir()


@directory_check
def check_win_cmake_no_unix_branch(d: Path) -> bool:
    """CMakeLists.txt should not have if(UNIX) branches."""
    cm = d / "CMakeLists.txt"
    if not cm.exists():
        return False
    text = cm.read_text(encoding="utf-8")
    return "if(UNIX)" not in text


@directory_check
def check_win_coverage_no_unix(d: Path) -> bool:
    """tests/CMakeLists.txt coverage section should not have UNIX."""
    tc = d / "tests" / "CMakeLists.txt"
    if not tc.exists():
        return False
    text = tc.read_text(encoding="utf-8")
    return "AND UNIX" not in text and "if(UNIX)" not in text