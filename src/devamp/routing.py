"""Parse agent routing recommendations from output files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# All valid agent names for routing
VALID_AGENTS = {"product", "architect", "planner", "dev", "qa"}

# Special routing values
ROUTING_PIPELINE = "pipeline"
ROUTING_DONE = "done"

VALID_NEXT_VALUES = VALID_AGENTS | {ROUTING_PIPELINE, ROUTING_DONE}


@dataclass
class RoutingRecommendation:
    """Parsed routing recommendation from an agent's output file."""

    next: str  # agent name, "pipeline", or "done"
    reason: str


def parse_routing(file_path: Path) -> RoutingRecommendation | None:
    """Parse ## Routing section from a markdown file.

    Expected format:
        ## Routing

        Next: <agent|pipeline|done>
        Reason: <text>

    Returns None if section not found or unparseable.
    """
    if not file_path.exists():
        return None

    text = file_path.read_text(encoding="utf-8")

    # Find ## Routing section
    match = re.search(
        r"^## Routing\s*\n(.*?)(?=\n## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None

    section = match.group(1)

    # Parse Next: and Reason: lines
    next_match = re.search(r"^Next:\s*(.+)$", section, re.MULTILINE)
    reason_match = re.search(r"^Reason:\s*(.+)$", section, re.MULTILINE)

    if not next_match:
        return None

    next_value = next_match.group(1).strip().lower()
    reason = reason_match.group(1).strip() if reason_match else ""

    if next_value not in VALID_NEXT_VALUES:
        return None

    return RoutingRecommendation(next=next_value, reason=reason)
