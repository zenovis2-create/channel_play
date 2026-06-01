"""Console rendering helpers."""

from __future__ import annotations


def yn(value: bool) -> str:
    return "yes" if value else "no"


def table(rows: list[tuple[str, str]]) -> str:
    width = max((len(left) for left, _ in rows), default=0)
    return "\n".join(f"{left:<{width}}  {right}" for left, right in rows)
