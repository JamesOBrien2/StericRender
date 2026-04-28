"""Shared visual helpers for steric-map SVG output."""

from __future__ import annotations

import base64
from io import BytesIO

import numpy as np
from PIL import Image

PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "sambvca": [
        (49, 48, 124),
        (45, 83, 164),
        (63, 143, 194),
        (70, 196, 221),
        (120, 197, 157),
        (188, 220, 54),
        (254, 235, 39),
        (251, 166, 38),
        (239, 66, 45),
        (177, 31, 43),
        (94, 18, 27),
    ],
    "terrain": [
        (43, 95, 127),
        (84, 158, 179),
        (242, 228, 166),
        (215, 132, 72),
        (142, 52, 47),
    ],
}


def color_for_value(value: float, vmin: float, vmax: float, palette: str = "sambvca") -> str:
    """Map a scalar value to a hex color."""
    stops = np.array(PALETTES[palette], dtype=float)
    if vmax <= vmin:
        t = 0.5
    else:
        t = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    scaled = t * (len(stops) - 1)
    i = int(np.floor(scaled))
    j = min(i + 1, len(stops) - 1)
    local = scaled - i
    rgb = (1 - local) * stops[i] + local * stops[j]
    return "#{:02x}{:02x}{:02x}".format(*(int(round(c)) for c in rgb))


def rgb_for_value(value: float, vmin: float, vmax: float, palette: str = "sambvca") -> tuple[int, int, int]:
    """Map a scalar value to an RGB tuple."""
    color = color_for_value(value, vmin, vmax, palette)
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def steric_map_image_svg(
    *,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    svg_x: float,
    svg_y: float,
    width: float,
    height: float,
    sphere_radius: float,
    vmin: float,
    vmax: float,
    palette: str = "sambvca",
    opacity: float = 1.0,
    pixels: int = 900,
    bands: int = 34,
) -> str:
    """Return an embedded PNG image for smooth filled steric-map colours."""
    data_uri = steric_map_png_data_uri(
        x=x,
        y=y,
        z=z,
        sphere_radius=sphere_radius,
        vmin=vmin,
        vmax=vmax,
        palette=palette,
        pixels=pixels,
        bands=bands,
    )
    return (
        f'<image class="stericrender-filled-map" x="{svg_x:.2f}" y="{svg_y:.2f}" '
        f'width="{width:.2f}" height="{height:.2f}" href="{data_uri}" '
        f'opacity="{opacity:.3f}" preserveAspectRatio="none"/>\n'
    )


def steric_map_png_data_uri(
    *,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    sphere_radius: float,
    vmin: float,
    vmax: float,
    palette: str = "sambvca",
    pixels: int = 900,
    bands: int = 34,
) -> str:
    """Encode the steric-map grid as a smooth circular RGBA PNG data URI."""
    image = steric_map_rgba(
        x=x,
        y=y,
        z=z,
        sphere_radius=sphere_radius,
        vmin=vmin,
        vmax=vmax,
        palette=palette,
        pixels=pixels,
        bands=bands,
    )
    buffer = BytesIO()
    Image.fromarray(image, mode="RGBA").save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def steric_map_rgba(
    *,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    sphere_radius: float,
    vmin: float,
    vmax: float,
    palette: str = "sambvca",
    pixels: int = 900,
    bands: int = 34,
) -> np.ndarray:
    """Sample a steric-map grid into a circular, banded RGBA image."""
    pixels = max(int(pixels), 32)
    bands = max(int(bands), 2)
    x0 = float(x[0])
    y0 = float(y[0])
    dx = float(x[1] - x[0]) if len(x) > 1 else 1.0
    dy = float(y[1] - y[0]) if len(y) > 1 else 1.0
    levels = np.linspace(vmin, vmax, bands)

    xx = -sphere_radius + (np.arange(pixels, dtype=float) + 0.5) / pixels * 2.0 * sphere_radius
    yy = sphere_radius - (np.arange(pixels, dtype=float) + 0.5) / pixels * 2.0 * sphere_radius
    grid_x, grid_y = np.meshgrid(xx, yy)
    distance = np.sqrt(grid_x * grid_x + grid_y * grid_y)
    pixel_width = 2.0 * sphere_radius / pixels
    alpha_mask = np.clip((sphere_radius - distance) / pixel_width + 0.5, 0.0, 1.0)
    circle = alpha_mask > 0.0

    fx = (grid_x - x0) / dx
    fy = (grid_y - y0) / dy
    ix = np.floor(fx).astype(int)
    iy = np.floor(fy).astype(int)
    inside = circle & (ix >= 0) & (iy >= 0) & (ix + 1 < len(x)) & (iy + 1 < len(y))

    values = np.full((pixels, pixels), np.nan, dtype=float)
    coverage = np.zeros((pixels, pixels), dtype=float)
    if np.any(inside):
        rows, cols = np.where(inside)
        ixv = ix[rows, cols]
        iyv = iy[rows, cols]
        tx = fx[rows, cols] - ixv
        ty = fy[rows, cols] - iyv
        vals = np.stack(
            [
                z[iyv, ixv],
                z[iyv, ixv + 1],
                z[iyv + 1, ixv],
                z[iyv + 1, ixv + 1],
            ],
            axis=1,
        )
        weights = np.stack(
            [
                (1.0 - tx) * (1.0 - ty),
                tx * (1.0 - ty),
                (1.0 - tx) * ty,
                tx * ty,
            ],
            axis=1,
        )
        finite_vals = np.isfinite(vals)
        finite_weights = np.where(finite_vals, weights, 0.0)
        weight_sum = finite_weights.sum(axis=1)
        finite = weight_sum > 0.0
        sampled = np.sum(np.where(finite_vals, vals, 0.0) * finite_weights, axis=1) / np.where(
            finite,
            weight_sum,
            1.0,
        )
        values[rows[finite], cols[finite]] = sampled[finite]
        coverage[rows[finite], cols[finite]] = weight_sum[finite]

    valid = np.isfinite(values)
    out = np.zeros((pixels, pixels, 4), dtype=np.uint8)
    if np.any(valid):
        clipped = np.clip(values[valid], vmin, vmax)
        nearest = np.abs(clipped[:, None] - levels[None, :]).argmin(axis=1)
        banded = levels[nearest]
        colors = np.array([rgb_for_value(float(value), vmin, vmax, palette) for value in banded], dtype=np.uint8)
        out[valid, :3] = colors
        alpha = alpha_mask[valid] * np.clip(coverage[valid], 0.0, 1.0)
        out[valid, 3] = np.round(255.0 * alpha).astype(np.uint8)
    return out


def colorbar_svg(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    vmin: float,
    vmax: float,
    palette: str = "sambvca",
    ticks: int = 7,
    font_size: int = 16,
) -> str:
    """Return a segmented horizontal SVG colorbar."""
    stops = PALETTES[palette]
    segment_w = width / len(stops)
    lines: list[str] = ['<g class="stericrender-colorbar">\n']
    for i in range(len(stops)):
        t = i / max(len(stops) - 1, 1)
        value = vmin + t * (vmax - vmin)
        lines.append(
            f'<rect x="{x + i * segment_w:.2f}" y="{y:.2f}" width="{segment_w + 0.2:.2f}" '
            f'height="{height:.2f}" fill="{color_for_value(value, vmin, vmax, palette)}"/>\n'
        )
    lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="none" stroke="#111827" stroke-width="1"/>\n')
    for i in range(ticks):
        t = i / max(ticks - 1, 1)
        value = vmin + t * (vmax - vmin)
        tx = x + t * width
        lines.append(f'<line x1="{tx:.2f}" y1="{y + height:.2f}" x2="{tx:.2f}" y2="{y + height + 6:.2f}" stroke="#111827" stroke-width="1"/>\n')
        lines.append(
            f'<text x="{tx:.2f}" y="{y + height + font_size + 7:.2f}" text-anchor="middle" '
            f'font-family="Arial,sans-serif" font-size="{font_size}" fill="#1f2933">{value:.1f}</text>\n'
        )
    lines.append(
        f'<text x="{x + width + 12:.2f}" y="{y + height + font_size + 7:.2f}" '
        f'font-family="Arial,sans-serif" font-size="{font_size}" fill="#1f2933">(A)</text>\n'
    )
    lines.append("</g>\n")
    return "".join(lines)


def contour_segments(x: np.ndarray, y: np.ndarray, z: np.ndarray, levels: np.ndarray) -> list[tuple[float, float, float, float]]:
    """Build contour line segments with a small marching-squares implementation."""
    segments: list[tuple[float, float, float, float]] = []
    for level in levels:
        for iy in range(len(y) - 1):
            for ix in range(len(x) - 1):
                vals = [
                    z[iy, ix],
                    z[iy, ix + 1],
                    z[iy + 1, ix + 1],
                    z[iy + 1, ix],
                ]
                if not np.isfinite(vals).all():
                    continue
                pts = [
                    (float(x[ix]), float(y[iy])),
                    (float(x[ix + 1]), float(y[iy])),
                    (float(x[ix + 1]), float(y[iy + 1])),
                    (float(x[ix]), float(y[iy + 1])),
                ]
                crossings: list[tuple[float, float]] = []
                for a in range(4):
                    b = (a + 1) % 4
                    va = float(vals[a])
                    vb = float(vals[b])
                    if (va < level and vb < level) or (va > level and vb > level) or va == vb:
                        continue
                    t = (level - va) / (vb - va)
                    px = pts[a][0] + t * (pts[b][0] - pts[a][0])
                    py = pts[a][1] + t * (pts[b][1] - pts[a][1])
                    crossings.append((px, py))
                if len(crossings) == 2:
                    segments.append((*crossings[0], *crossings[1]))
                elif len(crossings) == 4:
                    segments.append((*crossings[0], *crossings[1]))
                    segments.append((*crossings[2], *crossings[3]))
    return segments
