# AGENTS.md

This file is the repository-wide guide for AI coding agents working in
`cognite-sdk-python`.

Use it as the default source for repository-specific workflow, verification, and
change-shaping guidance. Human-oriented project context still lives in
`README.md` and `CONTRIBUTING.md`.

Tool-specific files may add extra instructions. Apply them in addition to this
file when relevant, for example `.gemini/styleguide.md` or
`.cursor/BUGBOT.md`.

## Purpose

Use this file to answer four questions quickly:

- What kind of repository is this?
- Where should changes be made?
- Which checks should be run before finishing?
- Which repository-specific rules are easy to miss?

## Guidance Layers

- Use `AGENTS.md` for durable repo-wide guidance.
- Use `.cursor/rules/` for scoped instructions tied to specific surfaces or
  workflows.
- Use `.cursor/BUGBOT.md` for repo-specific PR review guidance.
- Use `.cursor/mcp.json` and `.cursor/environment.json` for shared Cursor
  integration setup, not behavioral rules.
- Avoid duplicating the same instruction across `AGENTS.md` and
  `.cursor/rules/` unless the redundancy is intentional.

## Repository Overview

- This repository contains the Cognite Python SDK.
- Dependency management and packaging use Poetry.
- Local development is centered on Python 3.10, while CI also exercises newer
  Python versions.
- The SDK is async-first in v8: the async implementation is the source of
  truth, and the sync client is generated from it.
- The SDK also supports browser and Pyodide-based environments. Avoid assuming
  standard CPython-only behavior when touching imports, concurrency, file
  transfer, or packaging.

Useful paths:

- `cognite/client/_api/`: primary async API implementation
- `cognite/client/_cognite_client.py`: hand-maintained async client wiring
- `cognite/client/_sync_api/`: generated sync API wrappers
- `cognite/client/_sync_cognite_client.py`: generated sync client wiring
- `cognite/client/_proto/`: generated protobuf modules and type stubs
- `cognite/client/data_classes/`: SDK resource and data models
- `cognite/client/testing.py`: strict client mocks used by tests
- `tests/tests_unit/`: unit tests
- `tests/tests_integration/`: integration tests
- `docs/source/`: public documentation pages and docs test inputs
- `scripts/sync_client_codegen/`: async-to-sync code generation
- `scripts/toolkit/`: CDF auth group configuration and deployment inputs

## Where To Work

Prefer editing the async implementation first.

- Make API behavior changes in `cognite/client/_api/` and related
  hand-maintained modules.
- Treat `cognite/client/_sync_api/`, `cognite/client/_sync_cognite_client.py`,
  and `cognite/client/_proto/*.py` / `*.pyi` as generated output unless the
  task is explicitly about generators or generated sources.
- If you touch async API files, assume sync codegen verification is required.
- Do not hand-edit generated sync files as a shortcut for behavior changes.
- Follow existing module boundaries and naming conventions instead of creating
  new patterns.

When adding or reshaping public surface area, check the full wiring:

- `cognite/client/_cognite_client.py` for `AsyncCogniteClient` attributes
- `cognite/client/data_classes/__init__.py` for public data class exports
- `cognite/client/testing.py` for strict async/sync client mocks
- relevant docs pages under `docs/source/`

Repository-specific architecture rules:

- For nested APIs, keep one API class per file.
- For flat APIs, a single file directly under `cognite/client/_api/` is
  preferred.
- For nested API groups, add a directory instead of overloading a flat file.

## Code And Documentation Expectations

- Preserve strong typing. Use specific types instead of `Any` when possible.
- Match repository formatting and style settings from `pyproject.toml`.
- Keep lines within the configured Ruff limit of 120 characters.
- Use concise Google-style docstrings for public behavior where appropriate.
- Write comments sparingly and only when they add context that the code does
  not already communicate.
- Update docstrings and docs when public behavior, examples, or generated
  documentation should change.
- Public docs are page-based under `docs/source/`, not driven by a single
  `cognite.rst` file. Update the relevant page and `docs/source/index.rst` when
  a new page or toctree entry is needed.
- If you add docstring examples to a new module, update
  `tests/tests_unit/test_docstring_examples.py`. Its doctest coverage is
  explicit and allowlist-based, not automatic.
- If you change extras, packaging, or install guidance, keep `pyproject.toml`,
  `README.md`, `docs/source/index.rst`, and
  `docs/source/extensions_and_optional_dependencies.rst` aligned.

## Setup And Common Commands

Use Poetry-managed commands from the repository root.

```bash
poetry install -E all
pre-commit install
pre-commit run --all-files
pre-commit run --all-files --hook-stage manual
pytest tests/tests_unit
pytest tests/tests_unit/test_docstring_examples.py
pytest tests/tests_unit/test_utils/test_importing.py --test-deps-only-core
pytest tests/tests_integration
pytest docs
cd docs && make html
poetry build
python scripts/sync_client_codegen/main.py verify
python scripts/sync_client_codegen/main.py run --all-files
```

Notes:

- Use `poetry run ...` if your shell is not already inside the Poetry
  environment.
- `pre-commit` is not validation-only in this repo. It can rewrite tracked
  files through Ruff, custom docstring/example formatters, and sync codegen.
- Integration tests require the auth setup described in `CONTRIBUTING.md` and
  additional fixtures may require `cdf_principal.env`.
- CI also runs broader gates than the common local loop, including `test_core`,
  a multi-OS multi-Python test matrix, package builds, docs builds, sync
  codegen verification, and Pyodide wheel-install checks for browser-based
  workflows.

## Verification Before Finishing

Run the smallest relevant set of checks that proves the change is correct, but
do not skip linting or the relevant build/test command for the area you changed.

## Agent Validation Workflow

After making Python code changes, agents should use the repo validation command
instead of manually ordering individual linters:

```bash
python3 scripts/agent_checks.py fix
```

If this changes files, inspect the diff and continue from the updated state.

Before finishing Python work, run:

```bash
python3 scripts/agent_checks.py final
```

Run the smallest relevant `pytest` target for behavior changes.

For async API, client wiring, data class, testing mock, or generated-sync-sensitive
changes, ensure sync codegen is verified:

```bash
poetry run python scripts/sync_client_codegen/main.py verify
```

Final responses must report commands run, tests run, checks skipped with reasons,
and whether autofix or codegen changed files.

Minimum expectations by change type:

| Change type | Required checks |
| --- | --- |
| Python code changes | `pre-commit run --all-files` and the smallest relevant `pytest` target |
| Async API or sync-codegen-sensitive changes | Above, plus `python scripts/sync_client_codegen/main.py verify`; inspect generated diffs in `_sync_api/` and `_sync_cognite_client.py` |
| Docstring example changes in Python modules | `pre-commit run --all-files`, relevant unit coverage, and `pytest tests/tests_unit/test_docstring_examples.py` |
| `docs/source/` changes | `pre-commit run --all-files`, `pytest docs`, and `cd docs && make html` |
| Packaging, extras, import-path, or install-flow changes | `pre-commit run --all-files`, `poetry build`, update all public install docs, and consider `pytest tests/tests_unit/test_utils/test_importing.py --test-deps-only-core` |
| Integration-specific behavior | Relevant unit coverage first, then targeted integration tests that match the required auth flow and fixture setup |

Do not claim a task is complete without reporting which checks were run and
which were skipped.

## Testing Guidance

- Most behavior changes should include or update tests.
- Bug fixes should include a regression test whenever practical.
- Prefer targeted unit tests unless the behavior specifically depends on CDF
  integration.
- Doc examples are tested in more than one place:
  - docstring examples are exercised through
    `tests/tests_unit/test_docstring_examples.py`
  - `docs/source/` examples are exercised through `pytest docs`
  - rendered docs are validated separately through `cd docs && make html`
- Docstring doctests are not automatically discovered for every module. If you
  add examples to a new public module, update the allowlist in
  `tests/tests_unit/test_docstring_examples.py`.
- The `coredeps` path is opt-in and covers minimal-dependency import behavior.
  Use `--test-deps-only-core` when touching imports, optional dependencies, or
  extras behavior.
- Do not add redundant load/dump tests for subclasses of `CogniteResource` or
  `CogniteUpdate` when the base test coverage already handles that behavior.

## Repository-Specific Guardrails

- Async source files are authoritative; sync wrappers and the sync client are
  generated.
- Generated protobuf files under `cognite/client/_proto/` should not be edited
  manually unless the task is explicitly about protobuf generation.
- If a pre-commit hook or codegen step changes files, review the resulting diff
  and keep the generated updates that belong to the source change.
- Keep changes focused and consistent with nearby code rather than refactoring
  unrelated areas.
- Avoid introducing new dependencies unless they are clearly necessary and fit
  the existing packaging model.
- Preview and beta APIs often carry warning and versioning behavior through
  `FeaturePreviewWarning`, beta headers, or API subversions. Preserve those
  contracts when modifying preview features.
- When adding Cursor-specific repo artifacts such as `.cursor/rules/`,
  commands, MCP config, background-agent setup, Bugbot guidance, or skills,
  prefer the smallest addition that removes recurring engineer friction. Do
  not add agent scaffolding just because the platform supports it.
- Browser and Pyodide compatibility matters for this SDK. Packaging and runtime
  changes may need extra scrutiny beyond normal CPython tests.
- Changes under `scripts/toolkit/` are operationally important. When adding a
  new auth capability, update both the read-only and read-write group manifests
  and keep the deployment workflow in mind.
- Never commit secrets or hardcode credentials. Use environment variables for
  sensitive values.

## Pull Request Expectations

- Expect pull requests to include tests when behavior changes.
- Expect documentation updates when user-facing behavior or public APIs change.
- Pull request titles should follow Conventional Commits.
- For release-bearing changes, remember that release automation is driven by
  `fix`, `feat`, and breaking `fix!` / `feat!` / `perf!` titles.
- Breaking changes should be clearly identified in the title and description.

## Human-Friendly Rule Of Thumb

If an agent is unsure what to do next:

1. Read the relevant module, nearby tests, and public docs page first.
2. Edit the async source of truth, not generated sync or protobuf files.
3. Update public wiring, tests, and docs alongside behavior.
4. Run lint plus the smallest relevant test, build, docs, and codegen checks.
5. Report exactly what was verified and what remains unverified.
