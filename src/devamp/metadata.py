"""Task metadata — timestamps and session tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

METADATA_FILE = "task-metadata.json"


@dataclass
class TaskMetadata:
    """Operational metadata for a task (not pipeline state)."""

    created_at: str  # ISO 8601 timestamp
    sessions: dict[str, str] = field(default_factory=dict)  # agent_name → session_id
    last_routing_next: str | None = None  # last routing recommendation
    last_routing_reason: str | None = None


def _metadata_path(task_dir: Path) -> Path:
    return task_dir / METADATA_FILE


def load_metadata(task_dir: Path) -> TaskMetadata:
    """Load task metadata from JSON file. Returns defaults if file missing."""
    path = _metadata_path(task_dir)
    if not path.exists():
        return TaskMetadata(created_at=_now_iso())

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return TaskMetadata(
            created_at=data.get("created_at", _now_iso()),
            sessions=data.get("sessions", {}),
            last_routing_next=data.get("last_routing_next"),
            last_routing_reason=data.get("last_routing_reason"),
        )
    except (json.JSONDecodeError, KeyError):
        return TaskMetadata(created_at=_now_iso())


def save_metadata(task_dir: Path, meta: TaskMetadata) -> None:
    """Save task metadata to JSON file."""
    path = _metadata_path(task_dir)
    data = {
        "created_at": meta.created_at,
        "sessions": meta.sessions,
        "last_routing_next": meta.last_routing_next,
        "last_routing_reason": meta.last_routing_reason,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ensure_metadata(task_dir: Path) -> TaskMetadata:
    """Load metadata, create file if missing."""
    meta = load_metadata(task_dir)
    if not _metadata_path(task_dir).exists():
        save_metadata(task_dir, meta)
    return meta


def record_session(task_dir: Path, agent_name: str, session_id: str) -> None:
    """Record a session ID for an agent on this task."""
    meta = load_metadata(task_dir)
    meta.sessions[agent_name] = session_id
    save_metadata(task_dir, meta)


def record_routing(task_dir: Path, next_agent: str, reason: str) -> None:
    """Record the routing recommendation from the last agent."""
    meta = load_metadata(task_dir)
    meta.last_routing_next = next_agent
    meta.last_routing_reason = reason
    save_metadata(task_dir, meta)


def clear_routing(task_dir: Path) -> None:
    """Clear routing info before launching an agent.

    Prevents stale routing from persisting when an agent doesn't produce
    a ## Routing section (crash, user interrupt, agent forgot).
    """
    meta = load_metadata(task_dir)
    meta.last_routing_next = None
    meta.last_routing_reason = None
    save_metadata(task_dir, meta)


def get_session_id(task_dir: Path, agent_name: str) -> str | None:
    """Get stored session ID for an agent on this task."""
    meta = load_metadata(task_dir)
    return meta.sessions.get(agent_name)


def get_created_at(task_dir: Path) -> str:
    """Get task creation timestamp (human-readable short form)."""
    meta = load_metadata(task_dir)
    try:
        dt = datetime.fromisoformat(meta.created_at)
        return dt.strftime("%b %-d")
    except (ValueError, TypeError):
        return "?"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
