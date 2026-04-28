"""Rigid orientation helpers for steric maps."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OrientationResult:
    """Result of applying the StericRender orientation convention."""

    positions: np.ndarray
    rotation: np.ndarray
    center: np.ndarray
    measured_dihedral_degrees: float | None
    roll_degrees: float


def orient_positions(
    positions: np.ndarray,
    *,
    center_index: int,
    axis_indices: list[int],
    dihedral_indices: list[int] | None = None,
    dihedral_target_degrees: float = 0.0,
    flip_z: bool = False,
) -> OrientationResult:
    """Translate center to origin and align center-to-axis vector with +z.

    If dihedral indices are provided, the measured internal dihedral is used as
    a deterministic roll convention around z. Rigid rotation cannot alter an
    internal dihedral; the roll angle is ``target - measured``.
    """
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions must have shape (n_atoms, 3)")
    center = positions[center_index].copy()
    translated = positions - center
    axis_point = positions[axis_indices].mean(axis=0) - center
    if flip_z:
        axis_point = -axis_point
    z_axis = _normalize(axis_point, "axis vector")
    basis = _basis_from_z(z_axis)
    oriented = translated @ basis.T

    measured = None
    roll = 0.0
    if dihedral_indices is not None:
        measured = dihedral_degrees(oriented[dihedral_indices])
        roll = float(dihedral_target_degrees - measured)
        oriented = oriented @ _rotation_z(np.radians(roll)).T
        basis = _rotation_z(np.radians(roll)) @ basis

    return OrientationResult(oriented, basis, center, measured, roll)


def dihedral_degrees(points: np.ndarray) -> float:
    """Return the signed dihedral angle for four points in degrees."""
    if points.shape != (4, 3):
        raise ValueError("dihedral requires four 3D points")
    p0, p1, p2, p3 = points
    b0 = p0 - p1
    b1 = p2 - p1
    b2 = p3 - p2
    b1 = _normalize(b1, "dihedral central bond")
    v = b0 - np.dot(b0, b1) * b1
    w = b2 - np.dot(b2, b1) * b1
    x = np.dot(v, w)
    y = np.dot(np.cross(b1, v), w)
    return float(np.degrees(np.arctan2(y, x)))


def _basis_from_z(z_axis: np.ndarray) -> np.ndarray:
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, z_axis))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    x_axis = ref - np.dot(ref, z_axis) * z_axis
    x_axis = _normalize(x_axis, "x axis")
    y_axis = np.cross(z_axis, x_axis)
    return np.vstack([x_axis, y_axis, z_axis])


def _rotation_z(theta: float) -> np.ndarray:
    c = float(np.cos(theta))
    s = float(np.sin(theta))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _normalize(vector: np.ndarray, name: str) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-12:
        raise ValueError(f"Cannot normalize zero-length {name}")
    return vector / norm

