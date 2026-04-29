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
    xx, yy = np.meshgrid(xy, xy)  # shape (ny, nx): xx[iy,ix]=x[ix], yy[iy,ix]=y[iy]

    lateral2_grid = xx ** 2 + yy ** 2
    sphere_mask = lateral2_grid <= sphere_radius ** 2
    z_top = np.where(sphere_mask, np.sqrt(np.maximum(sphere_radius ** 2 - lateral2_grid, 0.0)), np.nan)

    z_values = np.full_like(z_top, np.nan)
    for position, radius in zip(positions, radii):
        dx = xx - position[0]
        dy = yy - position[1]
        lateral2 = dx ** 2 + dy ** 2
        r2 = float(radius) ** 2
        atom_mask = sphere_mask & (lateral2 <= r2)
        if not atom_mask.any():
            continue
        dz = np.sqrt(np.maximum(r2 - lateral2, 0.0))
        z_hit = np.minimum(position[2] + dz, z_top)
        valid = atom_mask & (z_hit >= -z_top)
        z_values = np.fmax(z_values, np.where(valid, z_hit, np.nan))

    return StericMapResult(xy, xy, z_values)
