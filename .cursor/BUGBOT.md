# Bugbot Review Guide

Review this repository as the Cognite Python SDK, not as a generic Python
package. Prioritize real regressions, missing verification, and public-surface
drift. Ignore style-only noise unless it hides a behavior problem.

## Focus Areas

1. Async source of truth vs generated sync output
   - Treat `cognite/client/_api/` and related async wiring as the source of
     truth.
   - Treat `cognite/client/_sync_api/`,
     `cognite/client/_sync_cognite_client.py`, and `cognite/client/_proto/`
     as generated unless the change is explicitly about codegen or protobuf
     generation.
   - Flag diffs that patch generated sync files directly without the matching
     async source change or codegen verification.

2. Public exports, examples, and docs drift
   - When public SDK behavior changes, check client wiring, exports, tests, and
     the relevant docs pages under `docs/source/`.
   - Flag user-facing changes that skip docstrings, docs pages, examples, or
     other public wiring that should have moved with the code.

3. Verification gaps
   - Flag missing `python scripts/sync_client_codegen/main.py verify` when
     async API or client-wiring changes could affect generated sync output.
   - Flag missing focused tests or docs validation when the diff touches docs,
     examples, packaging, imports, or install flows.

4. Packaging, import-path, browser, and Pyodide compatibility
   - Watch for regressions in extras, install guidance, optional dependencies,
     import behavior, and browser/Pyodide paths.
   - Flag changes that assume standard CPython-only behavior in areas where the
     repo supports browser-based execution.

5. Integration-runner auth manifests
   - If the diff adds or expands auth-dependent behavior under
     `scripts/toolkit/`, check that both the read-only and read-write auth
     group manifests stay aligned.

6. Cursor repo scaffolding
   - For diffs touching `.cursor/`, `.agents/plugins/`, or `plugins/`, focus on
     malformed JSON, dead paths, leaked secrets, non-portable assumptions, and
     accidental addition of commands, rules, or skills that this repo has
     intentionally not adopted yet.

## Avoid Noise

- Prefer substantive findings only.
- Skip formatting-only or speculative comments.
- Do not suggest repo-wide refactors unless the current diff makes a concrete
  bug or regression likely.
