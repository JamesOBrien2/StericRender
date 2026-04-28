"""Voxelized buried-volume calculation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BuriedVolumeResult:
    """Buried volume summary."""

    percent_buried: float
    buried_volume: float
    sphere_volume: float
    free_volume: float
    voxel_volume: float
    buried_voxels: int
    total_voxels: int
    quadrant_percent: dict[str, float]
    hemisphere_percent: dict[str, float]


def compute_buried_volume(
    positions: np.ndarray,
    radii: np.ndarray,
    *,
    sphere_radius: float = 3.5,
    mesh: float = 0.05,
) -> BuriedVolumeResult:
    """Compute percent buried volume within a sphere centered at the origin."""
    voxels = sphere_voxel_centers(sphere_radius, mesh)
    buried = classify_buried(voxels, positions, radii)
    voxel_volume = mesh**3
    buried_volume = float(buried.sum() * voxel_volume)
    sphere_volume = float(len(voxels) * voxel_volume)
    free_volume = sphere_volume - buried_volume
    percent = 100.0 * buried_volume / sphere_volume if sphere_volume else 0.0
    return BuriedVolumeResult(
        percent,
        buried_volume,
        sphere_volume,
        free_volume,
        voxel_volume,
        int(buried.sum()),
        int(len(voxels)),
        _region_percents(voxels, buried, voxel_volume, quadrant_masks(voxels)),
        _region_percents(voxels, buried, voxel_volume, hemisphere_masks(voxels)),
    )


def sphere_voxel_centers(radius: float, mesh: float) -> np.ndarray:
    """Return voxel centers inside a sphere."""
    coords = np.arange(-radius, radius + mesh * 0.5, mesh)
    x, y, z = np.meshgrid(coords, coords, coords, indexing="ij")
    points = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    return points[np.linalg.norm(points, axis=1) <= radius]


def classify_buried(voxels: np.ndarray, positions: np.ndarray, radii: np.ndarray) -> np.ndarray:
    """Classify voxels as buried if inside any atom radius."""
    buried = np.zeros(len(voxels), dtype=bool)
    for position, radius in zip(positions, radii):
        d2 = np.sum((voxels - position) ** 2, axis=1)
        buried |= d2 <= float(radius) ** 2
    return buried


def quadrant_masks(points: np.ndarray) -> dict[str, np.ndarray]:
    """Return XY quadrant masks."""
    x = points[:, 0]
    y = points[:, 1]
    return {
        "NE": (x >= 0) & (y >= 0),
        "NW": (x < 0) & (y >= 0),
        "SW": (x < 0) & (y < 0),
        "SE": (x >= 0) & (y < 0),
    }


def hemisphere_masks(points: np.ndarray) -> dict[str, np.ndarray]:
    """Return directional hemisphere masks."""
    x = points[:, 0]
    y = points[:, 1]
    return {
        "north": y >= 0,
        "south": y < 0,
        "east": x >= 0,
        "west": x < 0,
    }


def _region_percents(
    voxels: np.ndarray,
    buried: np.ndarray,
    voxel_volume: float,
    masks: dict[str, np.ndarray],
) -> dict[str, float]:
    values: dict[str, float] = {}
    for name, mask in masks.items():
        total = int(mask.sum())
        if total == 0:
            values[name] = 0.0
            continue
        values[name] = 100.0 * float(buried[mask].sum() * voxel_volume) / float(total * voxel_volume)
    return values
