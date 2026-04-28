#!/usr/bin/env python
"""Run StericRender validation checks against analytic and optional references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from stericrender.io import atoms_to_arrays, load_atoms
from stericrender.radii import radius_for_symbol
from stericrender.validation import analytic_centered_sphere_percent, morfeus_compare
from stericrender.volume import compute_buried_volume


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sambvca-xyz", help="Optional SambVca SI XYZ file containing reference structures")
    parser.add_argument("--output", default="validation_report.json")
    args = parser.parse_args()

    report = {
        "analytic": _analytic_cases(),
        "morfeus_simple": _morfeus_simple_case(),
        "sambvca_si": _sambvca_placeholder(args.sambvca_xyz),
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


def _analytic_cases() -> list[dict]:
    cases = []
    for atom_radius, sphere_radius in [(1.0, 2.0), (radius_for_symbol("C", "scaled-bondi"), 3.5)]:
        result = compute_buried_volume(
            np.array([[0.0, 0.0, 0.0]]),
            np.array([atom_radius]),
            sphere_radius=sphere_radius,
            mesh=0.05,
        )
        expected = analytic_centered_sphere_percent(atom_radius, sphere_radius)
        cases.append(
            {
                "atom_radius": atom_radius,
                "sphere_radius": sphere_radius,
                "stericrender_percent": result.percent_buried,
                "analytic_percent": expected,
                "delta_percent": result.percent_buried - expected,
            }
        )
    return cases


def _morfeus_simple_case() -> dict:
    try:
        import morfeus  # noqa: F401
    except ModuleNotFoundError:
        return {"status": "skipped", "reason": "morfeus-ml is not installed"}
    atoms = load_atoms(Path("examples/simple.xyz"))
    symbols, positions = atoms_to_arrays(atoms)
    comparison = morfeus_compare(
        symbols,
        positions,
        metal_index=1,
        excluded_atoms=[],
        sphere_radius=3.5,
        mesh=0.1,
        density=0.001,
    )
    return {
        "status": "ok",
        "stericrender_percent": comparison.stericrender_percent,
        "morfeus_percent": comparison.morfeus_percent,
        "delta_percent": comparison.delta_percent,
    }


def _sambvca_placeholder(path: str | None) -> dict:
    if not path:
        return {
            "status": "skipped",
            "reason": "pass --sambvca-xyz with om6b00371_si_002.xyz from the SambVca 2 supporting information",
        }
    input_path = Path(path)
    if not input_path.is_file():
        return {"status": "missing", "path": str(input_path)}
    structures = _read_multi_xyz_headers(input_path)
    return {
        "status": "available",
        "path": str(input_path),
        "structures": structures,
        "n_structures": len(structures),
        "note": "Reference structures are present. Add per-system center/axis/exclusion presets to validate published %VBur values.",
    }


def _read_multi_xyz_headers(path: Path) -> list[dict]:
    lines = path.read_text(errors="replace").splitlines()
    structures = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        try:
            n_atoms = int(line)
        except ValueError:
            i += 1
            continue
        title = lines[i + 1].strip() if i + 1 < len(lines) else ""
        structures.append({"index": len(structures) + 1, "n_atoms": n_atoms, "title": title})
        i += n_atoms + 2
    return structures


if __name__ == "__main__":
    main()
