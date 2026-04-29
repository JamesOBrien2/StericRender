"""SVG overlay generation for xyzrender molecular figures."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from stericrender.maps import StericMapResult
from stericrender.export import vbur_label_svg
from stericrender.visual import colorbar_svg, contour_segments, steric_map_edge_svg, steric_map_image_svg
from stericrender.volume import BuriedVolumeResult


def write_xyzrender_overlay_svg(
    *,
    oriented_xyz: str | Path,
    output_svg: str | Path,
    steric_map: StericMapResult,
    volume: BuriedVolumeResult,
    sphere_radius: float,
    render_config: str = "default",
    canvas_size: int = 800,
    zoom: float = 1.0,
    opacity: float = 0.72,
    color_range: tuple[float, float] | None = None,
    palette: str = "sambvca",
    show_contours: bool = True,
    show_colorbar: bool = True,
    show_vbur_label: bool = True,
    stereo: bool | list[str] = False,
    stereo_style: str = "atom",
) -> None:
    """Render an oriented molecule with xyzrender and composite the steric map.

    The oriented molecule is rendered with a fixed viewport centered on the
    steric-map origin. The overlay layer then uses the same orthographic
    projection convention as xyzrender: x to the right, y upward, z ignored for
    the 2D topographic map.
    """
    try:
        from xyzrender import load, render
        from xyzrender.config import build_config
    except ModuleNotFoundError as exc:
        raise RuntimeError("xyzrender is required for overlay SVG output") from exc

    cfg = build_config(render_config, canvas_size=canvas_size, orient=False)
    cfg.fixed_center = (0.0, 0.0)
    if zoom <= 0.0:
        raise ValueError("--zoom must be greater than 0")
    cfg.fixed_span = 2.0 * sphere_radius * zoom
    mol = load(oriented_xyz)
    molecule_svg = str(render(mol, config=cfg, orient=False, stereo=stereo, stereo_style=stereo_style))
    width, height = _svg_size(molecule_svg, default=canvas_size)
    scale = (canvas_size - 2.0 * cfg.padding) / cfg.fixed_span
    r = sphere_radius * scale
    if zoom > 1.0:
        molecule_svg = _clip_molecule_to_viewport(molecule_svg)
    else:
        molecule_svg = _clip_molecule_to_disk(molecule_svg, cx=width / 2.0, cy=height / 2.0, r=r)
    footer_height = 132 if show_colorbar else (64 if show_vbur_label else 0)
    molecule_svg = _expand_svg_height(molecule_svg, height + footer_height)
    layer = steric_overlay_layer(
        steric_map,
        volume,
        sphere_radius=sphere_radius,
        width=width,
        height=height,
        scale=scale,
        opacity=opacity,
        color_range=color_range,
        palette=palette,
        show_contours=show_contours,
        show_colorbar=show_colorbar,
        show_vbur_label=show_vbur_label,
    )
    Path(output_svg).write_text(_insert_before_close(molecule_svg, layer))


def steric_overlay_layer(
    steric_map: StericMapResult,
    volume: BuriedVolumeResult,
    *,
    sphere_radius: float,
    width: float,
    height: float,
    scale: float,
    opacity: float,
    color_range: tuple[float, float] | None = None,
    palette: str = "sambvca",
    show_contours: bool = True,
    show_colorbar: bool = True,
    show_vbur_label: bool = True,
) -> str:
    """Build an SVG group for the projected steric map."""
    finite = steric_map.z[np.isfinite(steric_map.z)]
    z_min, z_max = color_range or (-sphere_radius, sphere_radius)
    if not finite.size:
        z_min, z_max = -sphere_radius, sphere_radius

    def px(x: float) -> float:
        return width / 2.0 + x * scale

    def py(y: float) -> float:
        return height / 2.0 - y * scale

    lines = [
        '  <g id="stericrender-overlay" style="pointer-events:none">\n',
        "    <title>StericRender topographic steric map overlay</title>\n",
        f'    <g id="stericrender-map-layer" opacity="{opacity:.3f}">\n',
        steric_map_image_svg(
            x=steric_map.x,
            y=steric_map.y,
            z=steric_map.z,
            svg_x=width / 2.0 - sphere_radius * scale,
            svg_y=height / 2.0 - sphere_radius * scale,
            width=2.0 * sphere_radius * scale,
            height=2.0 * sphere_radius * scale,
            sphere_radius=sphere_radius,
            vmin=z_min,
            vmax=z_max,
            palette=palette,
            opacity=1.0,
            pixels=1000,
            bands=34,
        ),
        steric_map_edge_svg(
            x=steric_map.x,
            y=steric_map.y,
            z=steric_map.z,
            sx=px,
            sy=py,
            stroke_width=max(4.0, scale * 0.09),
        ),
    ]
    if show_contours and finite.size:
        levels = np.linspace(z_min, z_max, 17)[1:-1]
        lines.append('    <g class="stericrender-contours" opacity="0.82">\n')
        for x1, y1, x2, y2 in contour_segments(steric_map.x, steric_map.y, steric_map.z, levels):
            lines.append(
                f'      <line x1="{px(x1):.2f}" y1="{py(y1):.2f}" x2="{px(x2):.2f}" y2="{py(y2):.2f}" '
                'stroke="#111827" stroke-width="1.05" stroke-linecap="round"/>\n'
            )
        lines.append("    </g>\n")
    lines.append("    </g>\n")
    r = sphere_radius * scale
    cx = width / 2.0
    cy = height / 2.0
    lines.extend(
        [
            f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="#111827" stroke-width="1.6"/>\n',
            f'    <line x1="{cx-r:.2f}" y1="{cy:.2f}" x2="{cx+r:.2f}" y2="{cy:.2f}" stroke="#111827" stroke-width="1.1"/>\n',
            f'    <line x1="{cx:.2f}" y1="{cy-r:.2f}" x2="{cx:.2f}" y2="{cy+r:.2f}" stroke="#111827" stroke-width="1.1"/>\n',
        ]
    )
    if show_vbur_label:
        lines.append(vbur_label_svg(cx, height + 40.0, volume.percent_buried, value_size=25, label_size=21))
    if show_colorbar:
        bar_width = min(width - 80.0, 640.0)
        lines.append(
            colorbar_svg(
                x=(width - bar_width) / 2.0,
                y=height + 76.0,
                width=bar_width,
                height=16.0,
                vmin=z_min,
                vmax=z_max,
                palette=palette,
                font_size=14,
            )
        )
    lines.append("  </g>\n")
    return "".join(lines)

def _insert_before_close(svg: str, layer: str) -> str:
    marker = "</svg>"
    if marker not in svg:
        raise ValueError("xyzrender output did not contain closing </svg>")
    return svg.replace(marker, layer + marker, 1)


def _clip_molecule_to_disk(svg: str, *, cx: float, cy: float, r: float) -> str:
    match = re.match(r"(?s)(<svg\b[^>]*>\s*)(.*)(</svg>\s*)", svg)
    if not match:
        raise ValueError("xyzrender output did not contain a complete <svg> document")
    open_tag, body, close_tag = match.groups()
    background = ""
    bg_match = re.match(r'(?s)(\s*<rect\b[^>]*width="100%"[^>]*/>\s*)(.*)', body)
    if bg_match:
        background, body = bg_match.groups()
    clip_id = "stericrender-map-clip"
    defs = (
        f'  <defs><clipPath id="{clip_id}">'
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/>'
        "</clipPath></defs>\n"
    )
    return (
        open_tag
        + defs
        + background
        + f'  <g id="stericrender-molecule" clip-path="url(#{clip_id})">\n'
        + body
        + "  </g>\n"
        + close_tag
    )


def _clip_molecule_to_viewport(svg: str) -> str:
    """Wrap molecule content without clipping it to the steric-map disk."""
    match = re.match(r"(?s)(<svg\b[^>]*>\s*)(.*)(</svg>\s*)", svg)
    if not match:
        raise ValueError("xyzrender output did not contain a complete <svg> document")
    open_tag, body, close_tag = match.groups()
    background = ""
    bg_match = re.match(r'(?s)(\s*<rect\b[^>]*width="100%"[^>]*/>\s*)(.*)', body)
    if bg_match:
        background, body = bg_match.groups()
    return (
        open_tag
        + background
        + '  <g id="stericrender-molecule">\n'
        + body
        + "  </g>\n"
        + close_tag
    )


def _expand_svg_height(svg: str, height: float) -> str:
    def replace_viewbox(match: re.Match[str]) -> str:
        parts = match.group(1).replace(",", " ").split()
        if len(parts) != 4:
            return match.group(0)
        parts[3] = f"{height:.0f}"
        return f'viewBox="{" ".join(parts)}"'

    svg = re.sub(r'viewBox="([^"]+)"', replace_viewbox, svg, count=1)
    return re.sub(r'height="[^"]+"', f'height="{height:.0f}"', svg, count=1)


def _svg_size(svg: str, default: int) -> tuple[float, float]:
    viewbox = re.search(r'viewBox="([^"]+)"', svg)
    if viewbox:
        parts = [float(part) for part in viewbox.group(1).replace(",", " ").split()]
        if len(parts) == 4:
            return parts[2], parts[3]
    return float(default), float(default)
