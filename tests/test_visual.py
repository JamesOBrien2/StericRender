import numpy as np

from stericrender.maps import StericMapResult
from stericrender.export import write_map_svg
from stericrender.overlay import _clip_molecule_to_disk, steric_overlay_layer
from stericrender.visual import color_for_value, colorbar_svg, contour_segments, steric_map_image_svg, steric_map_rgba
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


def test_steric_map_image_svg_embeds_png_data_uri():
    x = np.array([-1.0, 0.0, 1.0])
    y = np.array([-1.0, 0.0, 1.0])
    z = np.array([[0.0, 0.5, 1.0], [0.5, 1.0, 0.5], [1.0, 0.5, 0.0]])

    svg = steric_map_image_svg(
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
        pixels=32,
    )

    assert 'class="stericrender-filled-map"' in svg
    assert "data:image/png;base64," in svg


def test_steric_map_rgba_antialiases_circular_edge():
    x = np.linspace(-1.0, 1.0, 5)
    y = np.linspace(-1.0, 1.0, 5)
    xx, yy = np.meshgrid(x, y)
    z = 1.0 - xx * xx - yy * yy
    z[xx * xx + yy * yy > 1.0] = np.nan

    image = steric_map_rgba(
        x=x,
        y=y,
        z=z,
        sphere_radius=1.0,
        vmin=-1.0,
        vmax=1.0,
        pixels=48,
    )

    alpha = image[:, :, 3]
    assert np.any(alpha == 255)
    assert np.any((alpha > 0) & (alpha < 255))


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
    assert 'class="stericrender-vbur-label"' in svg
    assert ">50.00</tspan>" in svg


def test_clip_molecule_to_disk_wraps_structure_but_keeps_background_unclipped():
    svg = '<svg viewBox="0 0 100 100" width="100" height="100">\n<rect width="100%" height="100%" fill="#fff"/>\n<circle cx="120" cy="50" r="10"/>\n</svg>'

    clipped = _clip_molecule_to_disk(svg, cx=50.0, cy=50.0, r=40.0)

    assert 'clipPath id="stericrender-map-clip"' in clipped
    assert '<g id="stericrender-molecule" clip-path="url(#stericrender-map-clip)">' in clipped
    assert clipped.index('<rect width="100%"') < clipped.index('id="stericrender-molecule"')
