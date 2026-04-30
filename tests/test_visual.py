from pathlib import Path

import numpy as np
import pytest

from stericrender.export import write_map_svg
from stericrender.maps import StericMapResult
from stericrender.overlay import (
    _clip_molecule_to_disk,
    _clip_molecule_to_viewport,
    _molecule_content_bottom,
    _overlay_footer_layout,
    steric_overlay_layer,
)
from stericrender.visual import (
    color_for_value,
    colorbar_svg,
    contour_segments,
    steric_map_edge_svg,
    steric_map_fill_svg,
)
from stericrender.volume import BuriedVolumeResult


def test_sambvca_palette_endpoints_are_distinct():
    low = color_for_value(-3.0, -3.0, 3.0, "sambvca")
    mid = color_for_value(0.0, -3.0, 3.0, "sambvca")
    high = color_for_value(3.0, -3.0, 3.0, "sambvca")
    assert low != mid != high
    assert low.startswith("#")


def test_colorbar_svg_contains_tick_labels():
    svg = colorbar_svg(x=0, y=0, width=100, height=10, vmin=-3, vmax=3, palette="sambvca")
    assert "-3.0" in svg
    assert "3.0" in svg


def test_steric_map_fill_svg_emits_vector_cells():
    x = np.array([-1.0, 0.0, 1.0])
    y = np.array([-1.0, 0.0, 1.0])
    z = np.array([[0.0, 0.5, 1.0], [0.5, 1.0, 0.5], [1.0, 0.5, 0.0]])

    svg = steric_map_fill_svg(
        x=x,
        y=y,
        z=z,
        svg_x=0.0,
        svg_y=0.0,
        width=100.0,
        height=100.0,
        sphere_radius=1.0,
        vmin=-1.0,
        vmax=1.0,
    )

    assert 'class="stericrender-filled-map"' in svg
    assert '<clipPath id="stericrender-map-fill-clip">' in svg
    assert "<path " in svg
    assert "<image " not in svg
    assert "data:image/png" not in svg


def test_steric_map_edge_svg_traces_finite_boundary():
    x = np.array([-1.0, 0.0, 1.0])
    y = np.array([-1.0, 0.0, 1.0])
    z = np.array([[1.0, 1.0, np.nan], [1.0, 1.0, np.nan], [np.nan, np.nan, np.nan]])

    svg = steric_map_edge_svg(
        x=x,
        y=y,
        z=z,
        sx=lambda value: 10.0 + value,
        sy=lambda value: 20.0 - value,
        stroke_width=3.0,
    )

    assert 'class="stericrender-map-edge-cleanup"' in svg
    assert 'stroke-width="3.00"' in svg
    assert 'stroke="#111827"' in svg
    assert 'stroke="#ffffff"' not in svg
    assert "Q " in svg
    assert "<path " in svg


def test_steric_map_fill_svg_skips_empty_cells():
    x = np.array([-1.0, 0.0, 1.0])
    y = np.array([-1.0, 0.0, 1.0])
    z = np.full((3, 3), np.nan)

    svg = steric_map_fill_svg(
        x=x,
        y=y,
        z=z,
        svg_x=0.0,
        svg_y=0.0,
        width=100.0,
        height=100.0,
        sphere_radius=1.0,
        vmin=-1.0,
        vmax=1.0,
    )

    assert "<path " not in svg
    assert "data:image/png" not in svg


def test_readme_steric_map_example_has_no_quadrant_labels():
    svg = Path("examples/images/sambvca/complex_04_meduphos_map.svg").read_text()
    assert ">NE</text>" not in svg
    assert ">NW</text>" not in svg
    assert ">SW</text>" not in svg
    assert ">SE</text>" not in svg


def test_contour_segments_find_crossing():
    x = np.array([0.0, 1.0])
    y = np.array([0.0, 1.0])
    z = np.array([[0.0, 1.0], [1.0, 0.0]])
    segments = contour_segments(x, y, z, np.array([0.5]))
    assert len(segments) == 2


def test_map_svg_quadrant_labels_are_opt_in(tmp_path):
    steric_map = StericMapResult(
        x=np.array([-1.0, 0.0, 1.0]),
        y=np.array([-1.0, 0.0, 1.0]),
        z=np.array([[np.nan, 0.0, np.nan], [1.0, 2.0, 1.0], [np.nan, 0.0, np.nan]]),
    )
    volume = BuriedVolumeResult(50.0, 1.0, 2.0, 1.0, 0.1, 10, 20, {}, {})
    default_path = tmp_path / "default.svg"
    labelled_path = tmp_path / "labelled.svg"

    write_map_svg(default_path, steric_map, volume, sphere_radius=1.0)
    write_map_svg(labelled_path, steric_map, volume, sphere_radius=1.0, show_quadrant_labels=True)

    default_svg = default_path.read_text()
    labelled_svg = labelled_path.read_text()
    assert "<image " not in default_svg
    assert "data:image/png" not in default_svg
    assert ">NE</text>" not in default_svg
    assert ">NW</text>" not in default_svg
    assert ">SW</text>" not in default_svg
    assert ">SE</text>" not in default_svg
    assert ">NE</text>" in labelled_svg
    assert ">NW</text>" in labelled_svg
    assert ">SW</text>" in labelled_svg
    assert ">SE</text>" in labelled_svg


def test_overlay_layer_includes_full_opacity_colorbar():
    steric_map = StericMapResult(
        x=np.array([-1.0, 0.0, 1.0]),
        y=np.array([-1.0, 0.0, 1.0]),
        z=np.array([[np.nan, 0.0, np.nan], [1.0, 2.0, 1.0], [np.nan, 0.0, np.nan]]),
    )
    volume = BuriedVolumeResult(50.0, 1.0, 2.0, 1.0, 0.1, 10, 20, {}, {})

    svg = steric_overlay_layer(
        steric_map,
        volume,
        sphere_radius=1.0,
        width=200.0,
        height=200.0,
        scale=80.0,
        opacity=0.72,
    )

    assert 'id="stericrender-map-layer" opacity="0.720"' in svg
    assert 'class="stericrender-colorbar"' in svg
    assert "<image " not in svg
    assert "data:image/png" not in svg
    assert svg.count('class="stericrender-vbur-label"') == 1
    assert ">50.00</tspan>" in svg


def test_overlay_layer_can_hide_vbur_label():
    steric_map = StericMapResult(
        x=np.array([-1.0, 0.0, 1.0]),
        y=np.array([-1.0, 0.0, 1.0]),
        z=np.array([[np.nan, 0.0, np.nan], [1.0, 2.0, 1.0], [np.nan, 0.0, np.nan]]),
    )
    volume = BuriedVolumeResult(50.0, 1.0, 2.0, 1.0, 0.1, 10, 20, {}, {})

    svg = steric_overlay_layer(
        steric_map,
        volume,
        sphere_radius=1.0,
        width=200.0,
        height=200.0,
        scale=80.0,
        opacity=0.72,
        show_vbur_label=False,
    )

    assert 'class="stericrender-vbur-label"' not in svg
    assert ">50.00</tspan>" not in svg


def test_overlay_footer_follows_zoomed_map_instead_of_viewport_bottom():
    layout = _overlay_footer_layout(
        height=800.0,
        sphere_radius=3.5,
        scale=67.857142857,
        show_colorbar=True,
        content_bottom=610.0,
    )

    assert layout.label_y == pytest.approx(677.5)
    assert layout.colorbar_y == pytest.approx(713.5)
    assert layout.total_height == pytest.approx(769.5)


def test_overlay_footer_respects_molecule_content_below_zoomed_map():
    layout = _overlay_footer_layout(
        height=800.0,
        sphere_radius=3.5,
        scale=67.857142857,
        show_colorbar=True,
        content_bottom=720.0,
    )

    assert layout.label_y == 760.0
    assert layout.colorbar_y == 796.0
    assert layout.total_height == 852.0


def test_molecule_content_bottom_uses_wrapped_primitives():
    svg = """<svg viewBox="0 0 800 800" width="800" height="800">
<rect width="100%" height="100%" fill="#fff"/>
<g id="stericrender-molecule">
  <line x1="100" y1="500" x2="200" y2="610" stroke-width="12"/>
  <circle cx="400" cy="650" r="30" stroke-width="8"/>
</g>
</svg>"""

    assert _molecule_content_bottom(svg) == 684.0


def test_clip_molecule_to_disk_wraps_structure_but_keeps_background_unclipped():
    svg = '<svg viewBox="0 0 100 100" width="100" height="100">\n<rect width="100%" height="100%" fill="#fff"/>\n<circle cx="120" cy="50" r="10"/>\n</svg>'

    clipped = _clip_molecule_to_disk(svg, cx=50.0, cy=50.0, r=40.0)

    assert 'clipPath id="stericrender-map-clip"' in clipped
    assert '<g id="stericrender-molecule" clip-path="url(#stericrender-map-clip)">' in clipped
    assert clipped.index('<rect width="100%"') < clipped.index('id="stericrender-molecule"')


def test_clip_molecule_to_viewport_does_not_add_disk_clip():
    svg = '<svg viewBox="0 0 100 100" width="100" height="100">\n<rect width="100%" height="100%" fill="#fff"/>\n<circle cx="120" cy="50" r="10"/>\n</svg>'

    clipped = _clip_molecule_to_viewport(svg)

    assert 'clipPath id="stericrender-map-clip"' not in clipped
    assert '<g id="stericrender-molecule">' in clipped
    assert clipped.index('<rect width="100%"') < clipped.index('id="stericrender-molecule"')
