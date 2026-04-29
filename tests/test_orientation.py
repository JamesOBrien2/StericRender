import numpy as np

from stericrender.orientation import dihedral_degrees, orient_positions


def test_orient_positions_aligns_axis_to_z():
    positions = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    result = orient_positions(positions, center_index=0, axis_indices=[1])
    axis = result.positions[1] - result.positions[0]
    axis = axis / np.linalg.norm(axis)
    assert np.allclose(axis, [0.0, 0.0, 1.0])


def test_dihedral_returns_float_angle():
    points = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 1.0],
        ]
    )
    assert abs(abs(dihedral_degrees(points)) - 90.0) < 1e-8
