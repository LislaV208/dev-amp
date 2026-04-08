"""Tests for routing module — parsing ## Routing from agent output files."""

from __future__ import annotations

from pathlib import Path

from devamp.routing import parse_routing


def test_parse_routing_valid(tmp_path: Path) -> None:
    f = tmp_path / "qa-session.md"
    f.write_text(
        "# QA Session\n\nSome content.\n\n## Routing\n\nNext: dev\nReason: 3 bugs found.\n"
    )
    result = parse_routing(f)
    assert result is not None
    assert result.next == "dev"
    assert result.reason == "3 bugs found."


def test_parse_routing_pipeline(tmp_path: Path) -> None:
    f = tmp_path / "spec.md"
    f.write_text("# Spec\n\n## Routing\n\nNext: pipeline\nReason: Default flow.\n")
    result = parse_routing(f)
    assert result is not None
    assert result.next == "pipeline"


def test_parse_routing_done(tmp_path: Path) -> None:
    f = tmp_path / "qa-session.md"
    f.write_text("# QA\n\n## Routing\n\nNext: done\nReason: All good.\n")
    result = parse_routing(f)
    assert result is not None
    assert result.next == "done"


def test_parse_routing_no_section(tmp_path: Path) -> None:
    f = tmp_path / "spec.md"
    f.write_text("# Spec\n\nJust a spec, no routing.\n")
    result = parse_routing(f)
    assert result is None


def test_parse_routing_invalid_next(tmp_path: Path) -> None:
    f = tmp_path / "spec.md"
    f.write_text("# Spec\n\n## Routing\n\nNext: nonexistent\nReason: nope\n")
    result = parse_routing(f)
    assert result is None


def test_parse_routing_missing_file(tmp_path: Path) -> None:
    f = tmp_path / "nonexistent.md"
    result = parse_routing(f)
    assert result is None


def test_parse_routing_no_reason(tmp_path: Path) -> None:
    f = tmp_path / "spec.md"
    f.write_text("# Spec\n\n## Routing\n\nNext: dev\n")
    result = parse_routing(f)
    assert result is not None
    assert result.next == "dev"
    assert result.reason == ""


def test_parse_routing_case_insensitive_next(tmp_path: Path) -> None:
    f = tmp_path / "spec.md"
    f.write_text("# Spec\n\n## Routing\n\nNext: Dev\nReason: test\n")
    result = parse_routing(f)
    assert result is not None
    assert result.next == "dev"


def test_parse_routing_at_end_of_file(tmp_path: Path) -> None:
    """Routing section at end of file without trailing newline."""
    f = tmp_path / "output.md"
    f.write_text("# Output\n\nContent here.\n\n## Routing\n\nNext: qa\nReason: Ready.")
    result = parse_routing(f)
    assert result is not None
    assert result.next == "qa"
