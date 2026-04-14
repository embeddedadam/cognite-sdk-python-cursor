#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / ".cursor" / "hooks" / "state" / "ruff-edited-files.json"
SUPPORTED_SUFFIXES = {".py", ".pyi"}
Payload = dict[str, object]
State = dict[str, list[str]]


def emit(payload: Payload | None = None) -> int:
    sys.stdout.write(json.dumps(payload or {}))
    return 0


def load_payload() -> Payload | None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def get_string(payload: Payload, key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def load_state() -> State:
    if not STATE_PATH.exists():
        return {}
    try:
        raw_state = json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw_state, dict):
        return {}

    state: State = {}
    for conversation_id, files in raw_state.items():
        if not isinstance(conversation_id, str) or not isinstance(files, list):
            continue
        state[conversation_id] = [file_path for file_path in files if isinstance(file_path, str)]
    return state


def save_state(state: State) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(f"{json.dumps(state, indent=2, sort_keys=True)}\n")


def clear_conversation(conversation_id: str) -> None:
    state = load_state()
    if conversation_id in state:
        state.pop(conversation_id, None)
        save_state(state)


def resolve_workspace_root(file_path: Path, payload: Payload) -> Path | None:
    workspace_roots = payload.get("workspace_roots")
    if isinstance(workspace_roots, list):
        for root in workspace_roots:
            if not isinstance(root, str):
                continue
            root_path = Path(root).resolve()
            try:
                file_path.relative_to(root_path)
            except ValueError:
                continue
            return root_path
    try:
        file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return None
    return PROJECT_ROOT


def record_edited_file(conversation_id: str, file_path: Path) -> None:
    state = load_state()
    files = {Path(existing_file).resolve() for existing_file in state.get(conversation_id, [])}
    files.add(file_path.resolve())
    state[conversation_id] = sorted(str(path) for path in files)
    save_state(state)


def get_edited_files(conversation_id: str) -> list[Path]:
    state = load_state()
    return [Path(file_path).resolve() for file_path in state.get(conversation_id, [])]


def to_project_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def run_quiet(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def run_ruff_fix(workspace_root: Path, relative_file_path: Path) -> None:
    run_quiet(
        ["poetry", "run", "ruff", "check", "--fix", "--force-exclude", str(relative_file_path)],
        cwd=workspace_root,
    )
    run_quiet(
        ["poetry", "run", "ruff", "format", "--force-exclude", str(relative_file_path)],
        cwd=workspace_root,
    )


def run_ruff_check(paths: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["poetry", "run", "ruff", "check", "--force-exclude", *[to_project_path(path) for path in paths]],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def trim_output(output: str, max_lines: int = 20) -> str:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join([*lines[:max_lines], "..."])


def build_followup_message(paths: list[Path], output: str) -> str:
    files = ", ".join(to_project_path(path) for path in paths[:5])
    if len(paths) > 5:
        files = f"{files}, ..."
    details = trim_output(output)
    if details:
        return f"Ruff still reports issues in files you edited. Fix them before finishing.\nFiles: {files}\n\n{details}"
    return f"Ruff still reports issues in files you edited. Fix them before finishing.\nFiles: {files}"


def handle_after_edit(payload: Payload) -> int:
    file_path_raw = get_string(payload, "file_path")
    if file_path_raw is None:
        return emit()

    file_path = Path(file_path_raw).resolve()
    if file_path.suffix not in SUPPORTED_SUFFIXES or not file_path.exists():
        return emit()

    workspace_root = resolve_workspace_root(file_path, payload)
    if workspace_root is None:
        return emit()

    conversation_id = get_string(payload, "conversation_id")
    if conversation_id is not None:
        record_edited_file(conversation_id, file_path)

    try:
        relative_file_path = file_path.relative_to(workspace_root)
    except ValueError:
        return emit()

    run_ruff_fix(workspace_root, relative_file_path)
    return emit()


def handle_stop(payload: Payload) -> int:
    if get_string(payload, "status") != "completed":
        return emit()

    conversation_id = get_string(payload, "conversation_id")
    if conversation_id is None:
        return emit()

    paths = [path for path in get_edited_files(conversation_id) if path.exists() and path.suffix in SUPPORTED_SUFFIXES]
    if not paths:
        clear_conversation(conversation_id)
        return emit()

    try:
        result = run_ruff_check(paths)
    except FileNotFoundError as error:
        return emit({"followup_message": f"Could not run Ruff stop guard: {error}."})

    if result.returncode == 0:
        clear_conversation(conversation_id)
        return emit()

    return emit({"followup_message": build_followup_message(paths, result.stdout)})


def main() -> int:
    payload = load_payload()
    if payload is None:
        return emit()

    hook_event_name = get_string(payload, "hook_event_name")
    if hook_event_name == "afterFileEdit" or "file_path" in payload:
        return handle_after_edit(payload)
    if hook_event_name == "stop" or "status" in payload:
        return handle_stop(payload)
    return emit()


if __name__ == "__main__":
    raise SystemExit(main())
