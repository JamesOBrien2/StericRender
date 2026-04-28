"""Explicit 1-based atom-index selector parsing."""

from __future__ import annotations


def parse_indices(spec: str | None, n_atoms: int) -> list[int]:
    """Parse a 1-based index/range spec into sorted 0-based indices."""
    if spec is None or not spec.strip():
        return []
    indices: set[int] = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start > end:
                raise ValueError(f"Invalid descending range: {part}")
            values = range(start, end + 1)
        else:
            values = [int(part)]
        for value in values:
            if value < 1 or value > n_atoms:
                raise ValueError(f"Atom index {value} outside valid range 1-{n_atoms}")
            indices.add(value - 1)
    return sorted(indices)


def parse_required_indices(spec: str, n_atoms: int, count: int | None = None) -> list[int]:
    """Parse required atom indices and optionally enforce exact count."""
    indices = parse_indices(spec, n_atoms)
    if not indices:
        raise ValueError("Expected at least one atom index")
    if count is not None and len(indices) != count:
        raise ValueError(f"Expected exactly {count} atom indices, got {len(indices)} from {spec!r}")
    return indices


def selected_or_default(include: str | None, exclude: str | None, n_atoms: int) -> list[int]:
    """Resolve include/exclude specs into 0-based atom indices."""
    selected = set(parse_indices(include, n_atoms)) if include else set(range(n_atoms))
    selected.difference_update(parse_indices(exclude, n_atoms))
    if not selected:
        raise ValueError("No atoms remain after applying include/exclude selectors")
    return sorted(selected)


def parse_frame_indices(spec: str | None, n_frames: int) -> list[int]:
    """Parse a 1-based frame selector into sorted 0-based indices."""
    if spec is None or not spec.strip() or spec.strip().lower() == "all":
        return list(range(n_frames))
    return parse_indices(spec, n_frames)
