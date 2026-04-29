"""Command-line interface for StericRender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from stericrender.export import write_grid_csv, write_grid_npz, write_json, write_map_svg
from stericrender.io import StructureFrame, arrays_to_atoms, atoms_to_arrays, load_structure_frames, write_xyz
from stericrender.maps import compute_steric_map
from stericrender.orientation import orient_positions
from stericrender.overlay import write_xyzrender_overlay_svg
from stericrender.radii import radii_for_symbols
from stericrender.selectors import parse_frame_indices, parse_required_indices, selected_or_default
from stericrender.visual import PALETTES
from stericrender.volume import compute_buried_volume


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] == "map":
        raw_argv = raw_argv[1:]
    args = parser.parse_args(raw_argv)
    run_map(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stericrender")
    parser.add_argument("input", help="Input structure supported by xyzrender.load(), or plain XYZ fallback")
    parser.add_argument("--center", required=True, help="1-based center atom index, usually the metal")
    parser.add_argument("--axis", required=True, help="1-based atom indices/ranges whose centroid defines +z")
    parser.add_argument("--dihedral", help="Four 1-based atom indices used for deterministic z-axis roll")
    parser.add_argument("--dihedral-target", type=float, default=0.0, help="Target roll angle in degrees")
    parser.add_argument("--flip-z", action="store_true", help="Reverse the center-to-axis vector")
    parser.add_argument("--include", help="Atoms included in steric analysis; default is all atoms")
    parser.add_argument("--exclude", help="Atoms excluded from steric analysis")
    parser.add_argument(
        "--radii",
        choices=["scaled-bondi", "bondi", "csd"],
        default="scaled-bondi",
        help="Atomic radii set",
    )
    parser.add_argument("--include-hydrogens", action="store_true", help="Include H atoms in steric analysis")
    parser.add_argument(
        "--sphere-radius",
        dest="base_sphere_radius",
        type=float,
        default=3.5,
        help="Base steric-map sphere radius in Angstrom",
    )
    parser.add_argument(
        "--radius",
        dest="radius_multiplier",
        type=float,
        default=1.0,
        help="Steric-map radius multiplier; --radius 2 doubles the base sphere radius",
    )
    parser.add_argument("--mesh", type=float, default=0.05, help="Voxel/map mesh spacing in Angstrom")
    parser.add_argument(
        "--visual-mesh",
        type=float,
        default=0.05,
        help="Topographic mesh spacing used for SVG maps and overlays; numeric grids still use --mesh",
    )
    parser.add_argument("--output-prefix", default="stericrender", help="Output path prefix")
    parser.add_argument("--frames", default="all", help='1-based frame selector for multi-XYZ input, e.g. "1,4-6"')
    parser.add_argument("--no-overlay", action="store_true", help="Skip xyzrender molecular overlay SVG")
    parser.add_argument(
        "--config",
        "--render-config",
        dest="render_config",
        default="default",
        help="xyzrender preset/config for overlay SVG, matching xyzrender --config",
    )
    parser.add_argument("--overlay-opacity", type=float, default=0.72, help="Steric-map overlay opacity")
    parser.add_argument("--overlay-canvas-size", type=int, default=800, help="Overlay SVG canvas size")
    parser.add_argument(
        "--zoom",
        type=float,
        default=1.0,
        help="Overlay zoom-out multiplier; values above 1 show more molecule around the same steric radius",
    )
    parser.add_argument(
        "--overlay-all-atoms",
        action="store_true",
        help="Render all oriented atoms in overlay SVGs, including atoms excluded from steric analysis",
    )
    parser.add_argument(
        "--stereo",
        nargs="?",
        const="",
        default=None,
        metavar="CLASSES",
        help=(
            "Add xyzrender stereochemistry labels to overlay SVGs. "
            "Optional comma-separated class filter: point, ez, axis, plane, helix. "
            "Omit CLASSES to show all."
        ),
    )
    parser.add_argument(
        "--stereo-style",
        default="atom",
        choices=["atom", "label"],
        help="xyzrender R/S label placement for overlay SVGs",
    )
    parser.add_argument(
        "--map-palette",
        choices=sorted(PALETTES),
        default="sambvca",
        help="Steric-map colour palette",
    )
    parser.add_argument(
        "--color-range",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="Steric-map colour scale range in Angstrom; default is -R R",
    )
    parser.add_argument("--no-colorbar", action="store_true", help="Hide colorbar on map and overlay SVGs")
    parser.add_argument("--no-vbur-label", action="store_true", help="Hide %%VBur label on overlay SVGs")
    parser.add_argument("--no-contours", action="store_true", help="Hide contour lines on map and overlay SVGs")
    parser.add_argument("--show-quadrants", action="store_true", help="Show NE/NW/SW/SE quadrant labels on map SVGs")
    return parser


def run_map(args: argparse.Namespace) -> None:
    frames = load_structure_frames(args.input)
    frame_indices = parse_frame_indices(args.frames, len(frames))
    multi = len(frame_indices) > 1
    summaries = []
    for frame_index in frame_indices:
        frame = frames[frame_index]
        prefix = _frame_prefix(Path(args.output_prefix), frame, multi)
        summaries.append(process_frame(args, frame, prefix))
    if multi:
        summary_path = Path(f"{args.output_prefix}_summary.json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n")
        print(f"Processed {len(summaries)} frame(s)")
        print(f"Wrote {summary_path}")


def process_frame(args: argparse.Namespace, frame: StructureFrame, prefix: Path) -> dict:
    if args.base_sphere_radius <= 0.0:
        raise ValueError("--sphere-radius must be greater than 0")
    if args.radius_multiplier <= 0.0:
        raise ValueError("--radius must be greater than 0")
    if args.zoom <= 0.0:
        raise ValueError("--zoom must be greater than 0")
    sphere_radius = args.base_sphere_radius * args.radius_multiplier

    symbols, positions = atoms_to_arrays(frame.atoms)
    n_atoms = len(frame.atoms)
    center = parse_required_indices(args.center, n_atoms, count=1)[0]
    axis = parse_required_indices(args.axis, n_atoms)
    dihedral = parse_required_indices(args.dihedral, n_atoms, count=4) if args.dihedral else None

    oriented = orient_positions(
        positions,
        center_index=center,
        axis_indices=axis,
        dihedral_indices=dihedral,
        dihedral_target_degrees=args.dihedral_target,
        flip_z=args.flip_z,
    )

    graph_selected = selected_or_default(args.include, args.exclude, n_atoms)
    selected = list(graph_selected)
    if not args.include_hydrogens:
        selected = [idx for idx in selected if symbols[idx].upper() != "H"]
    if not selected:
        raise ValueError("No atoms selected for steric analysis after hydrogen filtering")

    selected_symbols = [symbols[idx] for idx in selected]
    selected_positions = oriented.positions[selected]
    selected_radii = np.array(radii_for_symbols(selected_symbols, radii=args.radii), dtype=float)

    volume = compute_buried_volume(
        selected_positions,
        selected_radii,
        sphere_radius=sphere_radius,
        mesh=args.mesh,
    )
    steric_map = compute_steric_map(
        selected_positions,
        selected_radii,
        sphere_radius=sphere_radius,
        mesh=args.mesh,
    )

    prefix.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "input": str(args.input),
        "frame": frame.index,
        "frame_title": frame.title,
        "center": center + 1,
        "axis": [idx + 1 for idx in axis],
        "dihedral": [idx + 1 for idx in dihedral] if dihedral else None,
        "dihedral_target_degrees": args.dihedral_target,
        "measured_dihedral_degrees": oriented.measured_dihedral_degrees,
        "roll_degrees": oriented.roll_degrees,
        "flip_z": args.flip_z,
        "include": args.include,
        "exclude": args.exclude,
        "selected_atoms": [idx + 1 for idx in selected],
        "radii": args.radii,
        "include_hydrogens": args.include_hydrogens,
        "sphere_radius": sphere_radius,
        "base_sphere_radius": args.base_sphere_radius,
        "radius_multiplier": args.radius_multiplier,
        "mesh": args.mesh,
        "visual_mesh": args.visual_mesh,
        "zoom": args.zoom,
        "map_palette": args.map_palette,
        "color_range": args.color_range,
        "render_config": args.render_config,
        "show_quadrants": args.show_quadrants,
        "overlay_all_atoms": args.overlay_all_atoms,
        "stereo": args.stereo,
        "stereo_style": args.stereo_style,
        "show_vbur_label": not args.no_vbur_label,
    }
    write_json(prefix.with_suffix(".json"), volume, metadata)
    write_grid_csv(f"{prefix}_grid.csv", steric_map)
    write_grid_npz(f"{prefix}_grid.npz", steric_map)
    color_range = tuple(args.color_range) if args.color_range else None
    visual_map = steric_map
    if args.visual_mesh and args.visual_mesh < args.mesh:
        visual_map = compute_steric_map(
            selected_positions,
            selected_radii,
            sphere_radius=sphere_radius,
            mesh=args.visual_mesh,
        )
    write_map_svg(
        f"{prefix}_map.svg",
        visual_map,
        volume,
        sphere_radius=sphere_radius,
        color_range=color_range,
        palette=args.map_palette,
        show_colorbar=not args.no_colorbar,
        show_contours=not args.no_contours,
        show_quadrant_labels=args.show_quadrants,
    )
    oriented_xyz = Path(f"{prefix}_oriented.xyz")
    write_xyz(arrays_to_atoms(symbols, oriented.positions), oriented_xyz, title="StericRender oriented")
    if not args.no_overlay:
        overlay_xyz = oriented_xyz
        if not args.overlay_all_atoms:
            overlay_xyz = Path(f"{prefix}_overlay_atoms.xyz")
            overlay_indices = selected if args.include_hydrogens else graph_selected
            overlay_symbols = [symbols[idx] for idx in overlay_indices]
            overlay_positions = oriented.positions[overlay_indices]
            write_xyz(arrays_to_atoms(overlay_symbols, overlay_positions), overlay_xyz, title="StericRender overlay atoms")
        try:
            write_xyzrender_overlay_svg(
                oriented_xyz=overlay_xyz,
                output_svg=f"{prefix}_overlay.svg",
                steric_map=visual_map,
                volume=volume,
                sphere_radius=sphere_radius,
                render_config=args.render_config,
                canvas_size=args.overlay_canvas_size,
                zoom=args.zoom,
                include_hydrogens=args.include_hydrogens,
                opacity=args.overlay_opacity,
                color_range=color_range,
                palette=args.map_palette,
                show_contours=not args.no_contours,
                show_colorbar=not args.no_colorbar,
                show_vbur_label=not args.no_vbur_label,
                stereo=_parse_stereo_arg(args.stereo),
                stereo_style=args.stereo_style,
            )
        finally:
            if overlay_xyz != oriented_xyz:
                overlay_xyz.unlink(missing_ok=True)
    print(f"%VBur {volume.percent_buried:.2f}")
    print(f"Wrote {prefix.with_suffix('.json')}")
    print(f"Wrote {prefix}_map.svg")
    if not args.no_overlay:
        print(f"Wrote {prefix}_overlay.svg")
    return {"frame": frame.index, "prefix": str(prefix), "percent_buried": volume.percent_buried}


def _frame_prefix(base: Path, frame: StructureFrame, multi: bool) -> Path:
    if not multi:
        return base
    return base.parent / f"{base.name}_frame_{frame.index:03d}"


def _parse_stereo_arg(value: str | None) -> bool | list[str]:
    if value is None:
        return False
    if value == "":
        return True
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    main()
