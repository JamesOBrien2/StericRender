"""Topographic steric-map grid generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class StericMapResult:
    """Topographic steric-map grid."""

    x: np.ndarray
    y: np.ndarray
    z: np.ndarray


def compute_steric_map(
    positions: np.ndarray,
    radii: np.ndarray,
    *,
    sphere_radius: float = 3.5,
    mesh: float = 0.05,
) -> StericMapResult:
    """Compute first occupied z value scanning from +z for each x/y point."""
    xy = np.arange(-sphere_radius, sphere_radius + mesh * 0.5, mesh)
    z_values = np.full((len(xy), len(xy)), np.nan, dtype=float)

    for ix, x in enumerate(xy):
        for iy, y in enumerate(xy):
            if x * x + y * y > sphere_radius * sphere_radius:
                continue
            z_top = float(np.sqrt(max(sphere_radius * sphere_radius - x * x - y * y, 0.0)))
            candidates: list[float] = []
            for position, radius in zip(positions, radii):
                dx = x - position[0]
                dy = y - position[1]
                lateral2 = dx * dx + dy * dy
                radius2 = float(radius) ** 2
                if lateral2 > radius2:
                    continue
                dz = float(np.sqrt(radius2 - lateral2))
                z_hit = min(float(position[2] + dz), z_top)
                if z_hit >= -z_top:
                    candidates.append(z_hit)
            if candidates:
                z_values[iy, ix] = max(candidates)

    return StericMapResult(xy, xy, z_values)
