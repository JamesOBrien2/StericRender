"""SVG overlay generation for xyzrender molecular figures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from stericrender.export import vbur_label_svg
from stericrender.maps import StericMapResult
from stericrender.visual import colorbar_svg, contour_segments, steric_map_edge_svg, steric_map_image_svg
from stericrender.volume import BuriedVolumeResult


@dataclass(frozen=True)
class _OverlayFooterLayout:
    label_y: float
    colorbar_y: float | None
    total_height: float


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
    include_hydrogens: bool = False,
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

    cfg = build_config(render_config, canvas_size=canvas_size, orient=False, hy=include_hydrogens, bo=True)
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
    footer_layout = _overlay_footer_layout(
        height=height,
        sphere_radius=sphere_radius,
        scale=scale,
        show_colorbar=show_colorbar,
        content_bottom=_molecule_content_bottom(molecule_svg),
    )
    molecule_svg = _expand_svg_height(molecule_svg, footer_layout.total_height)
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
        footer_layout=footer_layout,
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
    footer_layout: _OverlayFooterLayout | None = None,
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
    if footer_layout is None:
        footer_layout = _overlay_footer_layout(
            height=height,
            sphere_radius=sphere_radius,
            scale=scale,
            show_colorbar=show_colorbar,
        )
    lines.extend(
        [
            f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="#111827" stroke-width="1.6"/>\n',
            f'    <line x1="{cx - r:.2f}" y1="{cy:.2f}" x2="{cx + r:.2f}" y2="{cy:.2f}" stroke="#111827" stroke-width="1.1"/>\n',
            f'    <line x1="{cx:.2f}" y1="{cy - r:.2f}" x2="{cx:.2f}" y2="{cy + r:.2f}" stroke="#111827" stroke-width="1.1"/>\n',
            vbur_label_svg(cx, footer_layout.label_y, volume.percent_buried, value_size=25, label_size=21),
        ]
    )
    if show_vbur_label:
        lines.append(vbur_label_svg(cx, height + 40.0, volume.percent_buried, value_size=25, label_size=21))
    if show_colorbar:
        assert footer_layout.colorbar_y is not None
        bar_width = min(width - 80.0, 640.0)
        lines.append(
            colorbar_svg(
                x=(width - bar_width) / 2.0,
                y=footer_layout.colorbar_y,
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


def _overlay_footer_layout(
    *,
    height: float,
    sphere_radius: float,
    scale: float,
    show_colorbar: bool,
    content_bottom: float | None = None,
) -> _OverlayFooterLayout:
    """Place overlay annotations after the visible map/molecule content."""
    map_bottom = height / 2.0 + sphere_radius * scale
    footer_anchor = max(map_bottom, content_bottom if content_bottom is not None else map_bottom)
    label_y = footer_anchor + 40.0
    if show_colorbar:
        colorbar_y = label_y + 36.0
        total_height = colorbar_y + 56.0
    else:
        colorbar_y = None
        total_height = label_y + 40.0
    return _OverlayFooterLayout(
        label_y=label_y,
        colorbar_y=colorbar_y,
        total_height=max(total_height, footer_anchor + 1.0),
    )


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
    defs = f'  <defs><clipPath id="{clip_id}"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/></clipPath></defs>\n'
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
    return open_tag + background + '  <g id="stericrender-molecule">\n' + body + "  </g>\n" + close_tag


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


def _molecule_content_bottom(svg: str) -> float | None:
    """Estimate the lower visible bound of xyzrender molecule primitives."""
    match = re.search(r'(?s)<g id="stericrender-molecule"[^>]*>(.*?)</g>', svg)
    body = match.group(1) if match else svg
    bottoms: list[float] = []
    for tag in re.findall(r"(?s)<(circle|ellipse|line|rect|path)\b([^>]*)>", body):
        name, attrs = tag
        stroke_pad = _float_attr(attrs, "stroke-width", default=0.0) / 2.0
        if name == "circle":
            cy = _float_attr(attrs, "cy")
            r = _float_attr(attrs, "r", default=0.0)
            if cy is not None:
                bottoms.append(cy + r + stroke_pad)
        elif name == "ellipse":
            cy = _float_attr(attrs, "cy")
            ry = _float_attr(attrs, "ry", default=0.0)
            if cy is not None:
                bottoms.append(cy + ry + stroke_pad)
        elif name == "line":
            ys = [_float_attr(attrs, "y1"), _float_attr(attrs, "y2")]
            finite_ys = [y for y in ys if y is not None]
            if finite_ys:
                bottoms.append(max(finite_ys) + stroke_pad)
        elif name == "rect":
            y = _float_attr(attrs, "y")
            rect_height = _float_attr(attrs, "height")
            if y is not None and rect_height is not None:
                bottoms.append(y + rect_height + stroke_pad)
        elif name == "path":
            d_match = re.search(r'\bd="([^"]*)"', attrs)
            if d_match:
                numbers = [
                    float(value) for value in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d_match.group(1))
                ]
                if len(numbers) >= 2:
                    bottoms.append(max(numbers[1::2]) + stroke_pad)
    return max(bottoms) if bottoms else None


def _float_attr(attrs: str, name: str, *, default: float | None = None) -> float | None:
    match = re.search(rf'\b{name}="([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)"', attrs)
    if not match:
        return default
    return float(match.group(1))
