"""Export helpers for maps and numeric results."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from stericrender.maps import StericMapResult
from stericrender.visual import colorbar_svg, contour_segments, steric_map_edge_svg, steric_map_image_svg
from stericrender.volume import BuriedVolumeResult


def write_json(path: str | Path, result: BuriedVolumeResult, metadata: dict) -> None:
    """Write numeric results and metadata to JSON."""
    payload = {
        "percent_buried": result.percent_buried,
        "buried_volume": result.buried_volume,
        "sphere_volume": result.sphere_volume,
        "free_volume": result.free_volume,
        "voxel_volume": result.voxel_volume,
        "buried_voxels": result.buried_voxels,
        "total_voxels": result.total_voxels,
        "quadrant_percent": result.quadrant_percent,
        "hemisphere_percent": result.hemisphere_percent,
        "metadata": metadata,
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_grid_csv(path: str | Path, steric_map: StericMapResult) -> None:
    """Write steric-map grid as long CSV."""
    with Path(path).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x", "y", "z"])
        for iy, y in enumerate(steric_map.y):
            for ix, x in enumerate(steric_map.x):
                z = steric_map.z[iy, ix]
                writer.writerow([f"{x:.6f}", f"{y:.6f}", "" if np.isnan(z) else f"{z:.6f}"])


def write_grid_npz(path: str | Path, steric_map: StericMapResult) -> None:
    """Write steric-map grid as compressed numpy arrays."""
    np.savez_compressed(path, x=steric_map.x, y=steric_map.y, z=steric_map.z)


def write_map_svg(
    path: str | Path,
    steric_map: StericMapResult,
    volume: BuriedVolumeResult,
    *,
    size: int = 720,
    sphere_radius: float = 3.5,
    color_range: tuple[float, float] | None = None,
    palette: str = "sambvca",
    show_colorbar: bool = True,
    show_contours: bool = True,
    show_quadrant_labels: bool = False,
) -> None:
    """Write a compact standalone SVG heat-map representation."""
    margin = 70
    colorbar_height = 70 if show_colorbar else 0
    plot_size = size - 2 * margin - colorbar_height
    finite = steric_map.z[np.isfinite(steric_map.z)]
    z_min, z_max = color_range or (-sphere_radius, sphere_radius)
    if not finite.size:
        z_min, z_max = -sphere_radius, sphere_radius

    def sx(x: float) -> float:
        return margin + (x + sphere_radius) / (2 * sphere_radius) * plot_size

    def sy(y: float) -> float:
        return margin + (sphere_radius - y) / (2 * sphere_radius) * plot_size

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n',
        '<rect width="100%" height="100%" fill="#ffffff"/>\n',
        "<style>text{font-family:Arial,sans-serif;fill:#1f2933} .small{font-size:14px}</style>\n",
        steric_map_image_svg(
            x=steric_map.x,
            y=steric_map.y,
            z=steric_map.z,
            svg_x=margin,
            svg_y=margin,
            width=plot_size,
            height=plot_size,
            sphere_radius=sphere_radius,
            vmin=z_min,
            vmax=z_max,
            palette=palette,
            opacity=0.96,
            pixels=1000,
            bands=34,
        ),
        steric_map_edge_svg(
            x=steric_map.x,
            y=steric_map.y,
            z=steric_map.z,
            sx=sx,
            sy=sy,
            stroke_width=max(4.0, plot_size / (2.0 * sphere_radius) * 0.09),
        ),
    ]
    if show_contours and finite.size:
        levels = np.linspace(z_min, z_max, 17)[1:-1]
        lines.append('<g class="stericrender-contours" opacity="0.82">\n')
        for x1, y1, x2, y2 in contour_segments(steric_map.x, steric_map.y, steric_map.z, levels):
            lines.append(
                f'<line x1="{sx(x1):.2f}" y1="{sy(y1):.2f}" x2="{sx(x2):.2f}" y2="{sy(y2):.2f}" '
                'stroke="#111827" stroke-width="1.15" stroke-linecap="round"/>\n'
            )
        lines.append("</g>\n")
    cx = sx(0.0)
    cy = sy(0.0)
    r_px = plot_size / 2
    lines.extend(
        [
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r_px:.2f}" fill="none" stroke="#1f2933" stroke-width="2"/>\n',
            f'<line x1="{margin}" y1="{cy:.2f}" x2="{size - margin}" y2="{cy:.2f}" stroke="#1f2933" stroke-width="1.2"/>\n',
            f'<line x1="{cx:.2f}" y1="{margin}" x2="{cx:.2f}" y2="{size - margin}" stroke="#1f2933" stroke-width="1.2"/>\n',
        ]
    )
    if show_quadrant_labels:
        lines.extend(
            [
                f'<text x="{margin + plot_size - 32}" y="{margin - 14}" class="small">NE</text>\n',
                f'<text x="{margin + 12}" y="{margin - 14}" class="small">NW</text>\n',
                f'<text x="{margin + 12}" y="{margin + plot_size + 24}" class="small">SW</text>\n',
                f'<text x="{margin + plot_size - 32}" y="{margin + plot_size + 24}" class="small">SE</text>\n',
            ]
        )
    lines.append(vbur_label_svg(cx, margin + plot_size + 52, volume.percent_buried, value_size=25, label_size=21))
    if show_colorbar:
        lines.append(
            colorbar_svg(
                x=margin + 10,
                y=size - margin + 28,
                width=size - 2 * margin - 20,
                height=18,
                vmin=z_min,
                vmax=z_max,
                palette=palette,
            )
        )
    lines.append("</svg>\n")
    Path(path).write_text("".join(lines))


def vbur_label_svg(
    x: float,
    y: float,
    percent_buried: float,
    *,
    value_size: int = 24,
    label_size: int = 20,
    fill: str = "#111827",
) -> str:
    """Return a compact typographic label for the buried-volume value."""
    sub_size = max(10, int(label_size * 0.58))
    return (
        f'<g class="stericrender-vbur-label" transform="translate({x:.2f} {y:.2f})">\n'
        f'  <text text-anchor="middle" font-family="Arial,sans-serif" fill="{fill}">'
        f'<tspan font-size="{label_size}" font-weight="600">%V</tspan>'
        f'<tspan font-size="{sub_size}" baseline-shift="sub" font-weight="600">Bur</tspan>'
        f'<tspan dx="9" font-size="{value_size}" font-weight="700">{percent_buried:.2f}</tspan>'
        "</text>\n"
        "</g>\n"
    )
