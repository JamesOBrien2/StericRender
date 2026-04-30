"""Shared visual helpers for steric-map SVG output."""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np

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


def steric_map_fill_svg(
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
    bands: int = 34,
    clip_id: str = "stericrender-map-fill-clip",
) -> str:
    """Return vector SVG paths for the filled steric-map colour field."""
    bands = max(int(bands), 2)
    levels = np.linspace(vmin, vmax, bands)
    paths_by_color: dict[str, list[str]] = defaultdict(list)

    def sx(value: float) -> float:
        return svg_x + (value + sphere_radius) / (2.0 * sphere_radius) * width

    def sy(value: float) -> float:
        return svg_y + (sphere_radius - value) / (2.0 * sphere_radius) * height

    def flush_run(color: str | None, x0: float | None, x1: float, top: float, bottom: float) -> None:
        if color is None or x0 is None:
            return
        paths_by_color[color].append(f"M {x0:.2f} {top:.2f} H {x1:.2f} V {bottom:.2f} H {x0:.2f} Z")

    for iy in range(len(y) - 1):
        top = sy(float(y[iy + 1]))
        bottom = sy(float(y[iy]))
        run_color: str | None = None
        run_start: float | None = None
        run_end = sx(float(x[0]))
        for ix in range(len(x) - 1):
            cell_values = np.array(
                [
                    z[iy, ix],
                    z[iy, ix + 1],
                    z[iy + 1, ix],
                    z[iy + 1, ix + 1],
                ],
                dtype=float,
            )
            finite_values = cell_values[np.isfinite(cell_values)]
            left = sx(float(x[ix]))
            right = sx(float(x[ix + 1]))
            if not finite_values.size:
                flush_run(run_color, run_start, run_end, top, bottom)
                run_color = None
                run_start = None
                run_end = right
                continue

            value = float(finite_values.mean())
            clipped = float(np.clip(value, vmin, vmax))
            banded = float(levels[np.abs(levels - clipped).argmin()])
            color = color_for_value(banded, vmin, vmax, palette)
            if color == run_color:
                run_end = right
                continue
            flush_run(run_color, run_start, run_end, top, bottom)
            run_color = color
            run_start = left
            run_end = right
        flush_run(run_color, run_start, run_end, top, bottom)

    cx = svg_x + width / 2.0
    cy = svg_y + height / 2.0
    r = min(width, height) / 2.0
    lines = [
        f'<g class="stericrender-filled-map" opacity="{opacity:.3f}">\n',
        f'<defs><clipPath id="{clip_id}"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/></clipPath></defs>\n',
        f'<g clip-path="url(#{clip_id})">\n',
    ]
    for color, commands in paths_by_color.items():
        lines.append(f'<path d="{" ".join(commands)}" fill="{color}" stroke="{color}" stroke-width="0.12"/>\n')
    lines.append("</g>\n</g>\n")
    return "".join(lines)


def steric_map_edge_svg(
    *,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    sx,
    sy,
    stroke_width: float,
    outline_width: float = 1.15,
    stroke: str = "#111827",
    outline: str = "#111827",
) -> str:
    """Return vector strokes that clean up finite/no-data map edges."""
    finite = np.isfinite(z).astype(float)
    segments = contour_segments(x, y, finite, np.array([0.5]))
    if not segments:
        return ""
    commands = " ".join(_svg_smooth_path(points, sx, sy) for points in _segments_to_polylines(segments))
    return (
        f'<g class="stericrender-map-edge-cleanup" fill="none" stroke-linecap="round" stroke-linejoin="round">\n'
        f'<path d="{commands}" stroke="{stroke}" stroke-width="{stroke_width:.2f}"/>\n'
        f'<path d="{commands}" stroke="{outline}" stroke-width="{outline_width:.2f}" opacity="0.82"/>\n'
        "</g>\n"
    )


def _segments_to_polylines(
    segments: list[tuple[float, float, float, float]],
    *,
    precision: int = 6,
) -> list[list[tuple[float, float]]]:
    """Connect unordered contour segments into drawable polylines."""
    endpoints: list[tuple[tuple[float, float], tuple[float, float]]] = []
    by_key: dict[tuple[float, float], list[int]] = defaultdict(list)
    for i, (x1, y1, x2, y2) in enumerate(segments):
        a = (round(float(x1), precision), round(float(y1), precision))
        b = (round(float(x2), precision), round(float(y2), precision))
        endpoints.append((a, b))
        by_key[a].append(i)
        by_key[b].append(i)

    used: set[int] = set()
    polylines: list[list[tuple[float, float]]] = []
    for start in range(len(endpoints)):
        if start in used:
            continue
        used.add(start)
        line: deque[tuple[float, float]] = deque(endpoints[start])
        for append_right in (True, False):
            while True:
                key = line[-1] if append_right else line[0]
                next_id = next((idx for idx in by_key[key] if idx not in used), None)
                if next_id is None:
                    break
                used.add(next_id)
                a, b = endpoints[next_id]
                other = b if a == key else a
                if append_right:
                    line.append(other)
                else:
                    line.appendleft(other)
        polylines.append(list(line))
    return polylines


def _svg_smooth_path(points: list[tuple[float, float]], sx, sy) -> str:
    """Build a lightly smoothed SVG path through a contour polyline."""
    if len(points) < 2:
        return ""
    coords = [(float(sx(x)), float(sy(y))) for x, y in points]
    if len(coords) == 2:
        (x1, y1), (x2, y2) = coords
        return f"M {x1:.2f} {y1:.2f} L {x2:.2f} {y2:.2f}"
    commands = [f"M {coords[0][0]:.2f} {coords[0][1]:.2f}"]
    for i in range(1, len(coords) - 1):
        x, y = coords[i]
        nx, ny = coords[i + 1]
        mx = (x + nx) / 2.0
        my = (y + ny) / 2.0
        commands.append(f"Q {x:.2f} {y:.2f} {mx:.2f} {my:.2f}")
    commands.append(f"L {coords[-1][0]:.2f} {coords[-1][1]:.2f}")
    return " ".join(commands)


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
    lines.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="none" stroke="#111827" stroke-width="1"/>\n'
    )
    for i in range(ticks):
        t = i / max(ticks - 1, 1)
        value = vmin + t * (vmax - vmin)
        tx = x + t * width
        lines.append(
            f'<line x1="{tx:.2f}" y1="{y + height:.2f}" x2="{tx:.2f}" y2="{y + height + 6:.2f}" stroke="#111827" stroke-width="1"/>\n'
        )
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


def contour_segments(
    x: np.ndarray, y: np.ndarray, z: np.ndarray, levels: np.ndarray
) -> list[tuple[float, float, float, float]]:
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
