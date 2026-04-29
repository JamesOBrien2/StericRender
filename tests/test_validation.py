import numpy as np
import pytest

from stericrender.radii import radius_for_symbol
from stericrender.validation import analytic_centered_sphere_percent, morfeus_compare
from stericrender.volume import compute_buried_volume


def test_centered_atom_matches_analytic_volume_at_fine_mesh():
    atom_radius = 1.0
    sphere_radius = 2.0
    result = compute_buried_volume(
        np.array([[0.0, 0.0, 0.0]]),
        np.array([atom_radius]),
        sphere_radius=sphere_radius,
        mesh=0.05,
    )
    expected = analytic_centered_sphere_percent(atom_radius, sphere_radius)
    assert abs(result.percent_buried - expected) < 0.35


def test_scaled_bondi_carbon_centered_atom_matches_analytic_volume():
    atom_radius = radius_for_symbol("C", radii="scaled-bondi")
    sphere_radius = 3.5
    result = compute_buried_volume(
        np.array([[0.0, 0.0, 0.0]]),
        np.array([atom_radius]),
        sphere_radius=sphere_radius,
        mesh=0.05,
    )
    expected = analytic_centered_sphere_percent(atom_radius, sphere_radius)
    assert abs(result.percent_buried - expected) < 0.35


def test_morfeus_reference_smoke_if_installed():
    pytest.importorskip("morfeus")
    symbols = ["Pd", "P", "C", "C", "C"]
    positions = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 2.2],
            [1.5, 0.0, 2.9],
            [-1.5, 0.0, 2.9],
            [0.0, 1.5, 2.9],
        ]
    )
    comparison = morfeus_compare(
        symbols,
        positions,
        metal_index=1,
        excluded_atoms=[],
        sphere_radius=3.5,
        mesh=0.1,
        density=0.001,
    )
    assert abs(comparison.delta_percent) < 1.5
