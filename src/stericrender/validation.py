"""Validation helpers against analytic and external reference calculations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stericrender.radii import radii_for_symbols
from stericrender.volume import compute_buried_volume


@dataclass(frozen=True)
class MorfeusComparison:
    """Comparison between StericRender and Morfeus buried volume."""

    stericrender_percent: float
    morfeus_percent: float
    delta_percent: float
    stericrender_quadrants: dict[str, float] | None
    morfeus_quadrants: dict[str, float] | None


def analytic_centered_sphere_percent(atom_radius: float, sphere_radius: float) -> float:
    """Exact buried percentage for a centered atom fully inside the sphere."""
    if atom_radius > sphere_radius:
        return 100.0
    return 100.0 * (atom_radius**3) / (sphere_radius**3)


def morfeus_compare(
    symbols: list[str],
    positions: np.ndarray,
    *,
    metal_index: int,
    excluded_atoms: list[int] | None = None,
    include_hydrogens: bool = False,
    sphere_radius: float = 3.5,
    mesh: float = 0.1,
    density: float = 0.001,
    z_axis_atoms: list[int] | None = None,
    xz_plane_atoms: list[int] | None = None,
) -> MorfeusComparison:
    """Compare StericRender voxel %VBur with Morfeus point-sphere %VBur.

    All atom indices passed to this function are 1-based to match Morfeus.
    """
    try:
        from morfeus import BuriedVolume
    except ModuleNotFoundError as exc:
        raise RuntimeError("morfeus-ml is required for Morfeus validation") from exc

    excluded = set(excluded_atoms or [])
    excluded.add(metal_index)
    comparison_positions = positions - positions[metal_index - 1]
    if z_axis_atoms is not None:
        comparison_positions = _orient_like_morfeus(
            comparison_positions,
            z_axis_atoms=[idx - 1 for idx in z_axis_atoms],
            xz_plane_atoms=[idx - 1 for idx in xz_plane_atoms] if xz_plane_atoms is not None else None,
        )

    selected = []
    for i, symbol in enumerate(symbols, start=1):
        if i in excluded:
            continue
        if not include_hydrogens and symbol.upper() == "H":
            continue
        selected.append(i - 1)

    steric_radii = np.array(radii_for_symbols([symbols[i] for i in selected], radii="scaled-bondi"))
    steric = compute_buried_volume(
        comparison_positions[selected],
        steric_radii,
        sphere_radius=sphere_radius,
        mesh=mesh,
    )

    morfeus = BuriedVolume(
        symbols,
        positions,
        metal_index,
        excluded_atoms=sorted(excluded - {metal_index}),
        include_hs=include_hydrogens,
        radius=sphere_radius,
        radii_type="bondi",
        radii_scale=1.17,
        density=density,
        z_axis_atoms=z_axis_atoms,
        xz_plane_atoms=xz_plane_atoms,
    )
    morfeus_percent = float(morfeus.fraction_buried_volume * 100.0)
    morfeus_quadrants = None
    steric_quadrants = None
    if z_axis_atoms is not None and xz_plane_atoms is not None:
        morfeus.octant_analysis()
        morfeus_quadrants = {
            "NE": float(morfeus.quadrants["percent_buried_volume"][1]),
            "NW": float(morfeus.quadrants["percent_buried_volume"][2]),
            "SW": float(morfeus.quadrants["percent_buried_volume"][3]),
            "SE": float(morfeus.quadrants["percent_buried_volume"][4]),
        }
        steric_quadrants = dict(steric.quadrant_percent)
    return MorfeusComparison(
        steric.percent_buried,
        morfeus_percent,
        steric.percent_buried - morfeus_percent,
        steric_quadrants,
        morfeus_quadrants,
    )


def _orient_like_morfeus(
    positions: np.ndarray,
    *,
    z_axis_atoms: list[int],
    xz_plane_atoms: list[int] | None,
) -> np.ndarray:
    """Orient coordinates to match Morfeus z/xz convention."""
    v1 = positions[z_axis_atoms].mean(axis=0)
    z_axis = -_normalize(v1)
    if xz_plane_atoms is None:
        ref = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(ref, z_axis))) > 0.9:
            ref = np.array([0.0, 1.0, 0.0])
        x_axis = _normalize(ref - np.dot(ref, z_axis) * z_axis)
        y_axis = np.cross(z_axis, x_axis)
    else:
        v2 = positions[xz_plane_atoms].mean(axis=0)
        y_axis = _normalize(np.cross(v2, v1))
        x_axis = _normalize(np.cross(y_axis, z_axis))
    basis = np.vstack([x_axis, y_axis, z_axis])
    return positions @ basis.T


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-12:
        raise ValueError("Cannot normalize zero-length vector")
    return vector / norm
