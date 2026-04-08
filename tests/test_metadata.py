"""Tests for metadata module — task metadata persistence."""

from __future__ import annotations

import json
from pathlib import Path

from devamp.metadata import (
    clear_routing,
    ensure_metadata,
    get_created_at,
    get_session_id,
    load_metadata,
    record_routing,
    record_session,
    save_metadata,
)


def test_load_metadata_missing_file(tmp_path: Path) -> None:
    meta = load_metadata(tmp_path)
    assert meta.created_at  # should have a default
    assert meta.sessions == {}
    assert meta.last_routing_next is None


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    meta = load_metadata(tmp_path)
    meta.sessions["dev"] = "abc-123"
    meta.last_routing_next = "qa"
    meta.last_routing_reason = "Ready for QA"
    save_metadata(tmp_path, meta)

    loaded = load_metadata(tmp_path)
    assert loaded.sessions == {"dev": "abc-123"}
    assert loaded.last_routing_next == "qa"
    assert loaded.last_routing_reason == "Ready for QA"


def test_ensure_metadata_creates_file(tmp_path: Path) -> None:
    assert not (tmp_path / "task-metadata.json").exists()
    meta = ensure_metadata(tmp_path)
    assert (tmp_path / "task-metadata.json").exists()
    assert meta.created_at


def test_ensure_metadata_preserves_existing(tmp_path: Path) -> None:
    data = {
        "created_at": "2026-01-15T10:00:00+00:00",
        "sessions": {"product": "sess-1"},
        "last_routing_next": None,
        "last_routing_reason": None,
    }
    (tmp_path / "task-metadata.json").write_text(json.dumps(data))

    meta = ensure_metadata(tmp_path)
    assert meta.created_at == "2026-01-15T10:00:00+00:00"
    assert meta.sessions == {"product": "sess-1"}


def test_record_session(tmp_path: Path) -> None:
    ensure_metadata(tmp_path)
    record_session(tmp_path, "dev", "session-xyz")
    assert get_session_id(tmp_path, "dev") == "session-xyz"


def test_record_session_overwrites(tmp_path: Path) -> None:
    ensure_metadata(tmp_path)
    record_session(tmp_path, "dev", "session-1")
    record_session(tmp_path, "dev", "session-2")
    assert get_session_id(tmp_path, "dev") == "session-2"


def test_get_session_id_missing(tmp_path: Path) -> None:
    ensure_metadata(tmp_path)
    assert get_session_id(tmp_path, "qa") is None


def test_record_routing(tmp_path: Path) -> None:
    ensure_metadata(tmp_path)
    record_routing(tmp_path, "dev", "3 bugs found")
    meta = load_metadata(tmp_path)
    assert meta.last_routing_next == "dev"
    assert meta.last_routing_reason == "3 bugs found"


def test_clear_routing(tmp_path: Path) -> None:
    """clear_routing should remove stale routing info."""
    ensure_metadata(tmp_path)
    record_routing(tmp_path, "dev", "some reason")
    clear_routing(tmp_path)
    meta = load_metadata(tmp_path)
    assert meta.last_routing_next is None
    assert meta.last_routing_reason is None


def test_clear_routing_preserves_sessions(tmp_path: Path) -> None:
    """clear_routing should not touch session data."""
    ensure_metadata(tmp_path)
    record_session(tmp_path, "dev", "sess-1")
    record_routing(tmp_path, "qa", "ready")
    clear_routing(tmp_path)
    assert get_session_id(tmp_path, "dev") == "sess-1"


def test_get_created_at_format(tmp_path: Path) -> None:
    data = {
        "created_at": "2026-04-08T12:00:00+00:00",
        "sessions": {},
        "last_routing_next": None,
        "last_routing_reason": None,
    }
    (tmp_path / "task-metadata.json").write_text(json.dumps(data))
    result = get_created_at(tmp_path)
    assert "Apr" in result
    assert "8" in result


def test_load_metadata_corrupt_json(tmp_path: Path) -> None:
    (tmp_path / "task-metadata.json").write_text("not json")
    meta = load_metadata(tmp_path)
    assert meta.created_at  # fallback defaults
    assert meta.sessions == {}
