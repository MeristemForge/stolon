# Stolon

Reusable AI skills that extend from one domain to another — like stolons in nature.

## Structure

```
stolon/
├── skills/
│   ├── c-project-init/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── setup.md        # Project scaffolding instructions
│   ├── c-project-build/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── build.md        # Build/test/coverage workflow
│   ├── c-project-debug/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── debug.md        # Three-tier debugging workflow
│   ├── c-project-commit/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── commit.md       # Pre-commit validation + message format
│   └── c-project-style/
│       ├── SKILL.md
│       └── references/
│           └── style.md        # C11 cross-platform code style guide
├── tests/
│   ├── run_eval.py             # Universal eval runner
│   ├── run_smoke.py            # Live smoke tests against real projects
│   ├── run_integration.py      # Cross-skill handoff validation
│   ├── run_regression.py       # Baseline diff against git ref
│   ├── run_diff.py             # Quick baseline diff tool
│   ├── README.md               # Eval harness documentation
│   └── evals/
│       ├── c-project-init/     # 5 prompts, 89 checks
│       ├── c-project-build/    # 14 prompts, 53 checks
│       ├── c-project-debug/    # 12 prompts, 53 checks
│       ├── c-project-commit/   # 8 prompts, 46 checks
│       ├── c-project-style/    # 17 prompts, 61 checks
│       └── integration/        # 8 prompts, 23 checks
├── .gitignore
└── LICENSE
```

## Skills

| Name | Reference | Trigger |
|------|-----------|---------|
| [c-project-init](skills/c-project-init/) | setup.md | Scaffold a new C project |
| [c-project-build](skills/c-project-build/) | build.md | Build, test, sanitizer, coverage |
| [c-project-debug](skills/c-project-debug/) | debug.md | Crash, segfault, hang investigation |
| [c-project-commit](skills/c-project-commit/) | commit.md | Stage, commit, amend, push |
| [c-project-style](skills/c-project-style/) | style.md | Write or review .c/.h files |

## Architecture

Each SKILL.md is a thin gate — four sections:

1. **description** (YAML frontmatter) — CSO trigger keywords for skill discovery
2. **When NOT to Use** — cross-references to sibling skills for routing
3. **STOP** — forces the agent to locate and `readFile` the heavy reference (`references/*.md`) before any action
4. **Mandatory Verification** — a checklist the agent must pass before reporting the task done (post-generation, post-build, post-edit, pre-commit, etc.)

All domain knowledge lives in the reference files, not in SKILL.md. SKILL.md stays lean — gate plus verification checklist — while the references can be 600+ lines.

## Usage

Copy `skills/` into your agent's skill directory (e.g. `~/.kiro/skills/`, `~/.claude/skills/`). Skills are self-contained and independent of each other.

## License

```
MIT License

Copyright (c) 2026-2036, Jin.Wu <wujin.developer@gmail.com>

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
```
