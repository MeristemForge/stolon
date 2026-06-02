"""Deterministic checks for c-project-style skill eval.

Each check function:
  - Named check_<name> matching the id in prompts.json expected_checks
  - Returns True (pass) or False (fail)
  - Has an 'input_type' attribute: "text" for output text
"""

import re


def text_check(fn):
    fn.input_type = "text"
    return fn


# --- Public function naming ---


@text_check
def check_public_func_has_project_prefix(text: str) -> bool:
    """Public function name must start with project prefix (xylem_)."""
    return bool(re.search(r"\bxylem_\w+", text))


@text_check
def check_public_func_has_module_segment(text: str) -> bool:
    """Public function must include module segment (e.g. xylem_tcp_)."""
    return bool(re.search(r"\bxylem_tcp_\w+", text))


@text_check
def check_public_func_uses_snake_case(text: str) -> bool:
    """Public function names use snake_case."""
    match = re.search(r"\bxylem_tcp_(\w+)", text)
    if not match:
        return False
    action = match.group(1)
    return action == action.lower()


# --- Static callback naming ---


@text_check
def check_static_cb_has_underscore_prefix(text: str) -> bool:
    """Static callbacks start with underscore prefix."""
    return bool(re.search(r"\b_tcp_\w+_cb\b", text))


@text_check
def check_static_cb_has_cb_suffix(text: str) -> bool:
    """Static callbacks end with _cb suffix."""
    return bool(re.search(r"_cb\b", text))


@text_check
def check_static_cb_no_project_prefix(text: str) -> bool:
    """Static callbacks should NOT have the project prefix."""
    lower = text.lower()
    return (
        "_tcp_" in lower
        and not bool(re.search(r"\bxylem_tcp_\w+_cb\b", text))
    )


# --- Header guards ---


@text_check
def check_recommends_pragma_once(text: str) -> bool:
    """Should recommend _Pragma("once")."""
    return '_Pragma("once")' in text or "_Pragma" in text or "pragma once" in text.lower()


@text_check
def check_no_ifndef_guards(text: str) -> bool:
    """Should advise against #ifndef guards."""
    lower = text.lower()
    return (
        ("not" in lower or "don't" in lower or "avoid" in lower
         or "instead" in lower or "no " in lower)
        and ("#ifndef" in text or "ifndef" in lower)
    )


# --- Include ordering ---


@text_check
def check_mentions_own_header_first(text: str) -> bool:
    """Own module header should come first."""
    lower = text.lower()
    return "own" in lower or "module" in lower or "first" in lower


@text_check
def check_mentions_grouped_includes(text: str) -> bool:
    """Includes should be grouped with blank lines."""
    lower = text.lower()
    return "group" in lower or "blank line" in lower or "separate" in lower


@text_check
def check_mentions_stdlib_last(text: str) -> bool:
    """Standard library headers come last."""
    lower = text.lower()
    return "standard" in lower or "stdlib" in lower or "<stdio" in text or "<string" in text


# --- Memory lifecycle ---


@text_check
def check_mentions_create_destroy_for_opaque(text: str) -> bool:
    """create/destroy for opaque types (module owns memory)."""
    lower = text.lower()
    return "create" in lower and "destroy" in lower and "opaque" in lower


@text_check
def check_mentions_init_deinit_for_caller_owned(text: str) -> bool:
    """init/deinit for caller-owned memory."""
    lower = text.lower()
    return "init" in lower and "deinit" in lower and (
        "caller" in lower or "stack" in lower or "embed" in lower
        or "intrusive" in lower
    )


@text_check
def check_mentions_malloc_ownership(text: str) -> bool:
    """Should explain memory ownership distinction."""
    lower = text.lower()
    return (
        ("malloc" in lower or "alloc" in lower or "owns" in lower
         or "ownership" in lower)
    )


# --- Adding modules ---


@text_check
def check_mentions_public_header_path(text: str) -> bool:
    """Should mention include/<project>/<project>-<module>.h path."""
    return bool(re.search(r"include/\w+/\w+-\w+\.h", text))


@text_check
def check_mentions_src_implementation(text: str) -> bool:
    """Should mention src/<project>-<module>.c path."""
    return bool(re.search(r"src/\w+-\w+\.c", text))


@text_check
def check_mentions_add_to_srcs(text: str) -> bool:
    """Should mention adding to SRCS in CMakeLists.txt."""
    return "SRCS" in text or "CMakeLists" in text


@text_check
def check_mentions_umbrella_header(text: str) -> bool:
    """Should mention including in the umbrella header."""
    lower = text.lower()
    return "umbrella" in lower or (
        "include" in lower and ".h" in text
        and ("xylem.h" in text or "project" in lower)
    )


@text_check
def check_mentions_test_file(text: str) -> bool:
    """Should mention creating test-<module>.c."""
    return bool(re.search(r"test-\w+\.c", text))


@text_check
def check_mentions_add_test_cmake(text: str) -> bool:
    """Should mention adding test to tests/CMakeLists.txt."""
    return "add_test" in text or "CMakeLists" in text


# --- Banned functions ---


@text_check
def check_bans_sprintf(text: str) -> bool:
    """Should ban sprintf."""
    lower = text.lower()
    return "sprintf" in lower and (
        "ban" in lower or "forbidden" in lower or "restrict" in lower
        or "not" in lower or "don't" in lower or "avoid" in lower
        or "instead" in lower or "replace" in lower or "use snprintf" in lower
    )


@text_check
def check_bans_strcpy(text: str) -> bool:
    """Should ban strcpy."""
    lower = text.lower()
    return "strcpy" in lower and (
        "ban" in lower or "forbidden" in lower or "restrict" in lower
        or "not" in lower or "don't" in lower or "avoid" in lower
        or "instead" in lower or "replace" in lower or "use snprintf" in lower
    )


@text_check
def check_recommends_snprintf(text: str) -> bool:
    """Should recommend snprintf as replacement."""
    return "snprintf" in text


# --- Logging ---


@text_check
def check_log_uses_module_tag(text: str) -> bool:
    """Log message must start with the module name as an angle-bracket tag."""
    return bool(re.search(r'"<udp>', text)) or bool(re.search(r"<udp>", text))


@text_check
def check_log_uses_loge(text: str) -> bool:
    """Error logs use the loge (error) level, not logd/logi/logw."""
    return bool(re.search(r"\b\w*_?loge\b", text))


@text_check
def check_log_is_key_value_style(text: str) -> bool:
    """Log messages use key=value pairs (e.g. port=%d), not prose."""
    return bool(re.search(r"\w+=%[diuxsp]", text))


@text_check
def check_log_not_sentence_style(text: str) -> bool:
    """Log message inside loge() must not be a verbose sentence.

    Heuristic: the format string should be short and not contain
    sentence-like phrasing ("has failed", "the ", trailing period).
    """
    matches = re.findall(r'_?loge\(\s*"([^"]*)"', text)
    if not matches:
        return False
    for fmt in matches:
        lower = fmt.lower()
        if " the " in lower or " has " in lower or " a new " in lower:
            return False
        if fmt.rstrip().endswith("."):
            return False
    return True


# --- Comment style ---


@text_check
def check_uses_c_style_comments(text: str) -> bool:
    """Should recommend /* */ style comments."""
    return "/*" in text and "*/" in text


@text_check
def check_no_cpp_style_comments(text: str) -> bool:
    """Should advise against // comments."""
    lower = text.lower()
    return "//" in text and (
        "not" in lower or "don't" in lower or "avoid" in lower
        or "no " in lower or "instead" in lower or "forbidden" in lower
    )


@text_check
def check_mentions_ascii_only(text: str) -> bool:
    """Should mention ASCII-only requirement."""
    return "ASCII" in text or "ascii" in text


# --- Platform layer ---


@text_check
def check_platform_code_in_platform_dir(text: str) -> bool:
    """Platform-specific code must be in src/platform/."""
    return "src/platform" in text or "platform/" in text


@text_check
def check_no_ifdefs_outside_platform(text: str) -> bool:
    """Should warn against #ifdef outside platform dir."""
    lower = text.lower()
    return (
        ("#ifdef" in text or "ifdef" in lower or "conditional" in lower)
        and ("platform" in lower)
        and ("not" in lower or "don't" in lower or "only" in lower
             or "must" in lower or "outside" in lower or "exclusively" in lower)
    )


@text_check
def check_mentions_platform_prefix(text: str) -> bool:
    """Platform functions use platform_ prefix."""
    return "platform_" in text


# --- Test code rules ---


@text_check
def check_uses_custom_assert(text: str) -> bool:
    """Should mention the custom ASSERT macro."""
    return "ASSERT" in text and (
        '"assert.h"' in text or "custom" in text.lower()
        or "project" in text.lower() or "tests/assert" in text
    )


@text_check
def check_no_standard_assert(text: str) -> bool:
    """Should warn against <assert.h>."""
    return "<assert.h>" in text and (
        "not" in text.lower() or "don't" in text.lower()
        or "avoid" in text.lower() or "instead" in text.lower()
        or "no " in text.lower()
    )


@text_check
def check_one_concern_per_test(text: str) -> bool:
    """Each test function should test one behavior."""
    lower = text.lower()
    return (
        "one" in lower and (
            "concern" in lower or "behavior" in lower
            or "thing" in lower or "scenario" in lower
        )
    ) or "single" in lower


@text_check
def check_no_global_state_in_tests(text: str) -> bool:
    """Tests should not use global/file-scope mutable state."""
    lower = text.lower()
    return (
        ("global" in lower or "file-scope" in lower or "shared" in lower)
        and ("state" in lower or "variable" in lower or "mutable" in lower)
    )


@text_check
def check_mentions_add_test_helper(text: str) -> bool:
    """Should mention the <project>_add_test() CMake helper."""
    return "add_test" in text


# --- Negative ---


@text_check
def check_no_c_style_content(text: str) -> bool:
    """Unrelated prompts should not produce C style content."""
    return not bool(
        re.search(
            r"clang-format|ASSERT|snprintf|_Pragma|CMakeLists|platform_",
            text,
        )
    )


# --- Adversarial checks ---

@text_check
def check_rejects_cpp_comments(text: str) -> bool:
    """When asked to use // comments, agent must refuse and recommend /* */."""
    return "/*" in text and "*/" in text


@text_check
def check_rejects_pragma_once_raw(text: str) -> bool:
    """When asked about #pragma once, agent must recommend _Pragma instead."""
    return '_Pragma("once")' in text or "_Pragma" in text


@text_check
def check_explains_pragma_reason(text: str) -> bool:
    """Agent should explain why _Pragma is used instead of #pragma once."""
    lower = text.lower()
    return (
        ("_pragma" in lower or '_pragma("once")' in lower)
        and ("instead" in lower or "not" in lower or "use" in lower
             or "project" in lower or "convention" in lower)
    )
