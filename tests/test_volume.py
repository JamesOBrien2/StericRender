import numpy as np

from stericrender.maps import compute_steric_map
from stericrender.volume import compute_buried_volume


def test_buried_volume_is_positive_for_atom_at_origin():
    result = compute_buried_volume(
        np.array([[0.0, 0.0, 0.0]]),
        np.array([1.0]),
        sphere_radius=2.0,
        mesh=0.5,
    )
    assert result.percent_buried > 0.0
    assert result.buried_voxels > 0
    assert set(result.quadrant_percent) == {"NE", "NW", "SW", "SE"}


def test_steric_map_has_finite_values_for_atom_at_origin():
    result = compute_steric_map(
        np.array([[0.0, 0.0, 0.0]]),
        np.array([1.0]),
        sphere_radius=2.0,
        mesh=0.5,
    )
    assert np.isfinite(result.z).any()
