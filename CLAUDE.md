# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode (with test dependencies)
pip install -e ".[test]"

# Install with morfeus-ml for numeric validation against reference values
pip install -e ".[test,validation]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_volume.py

# Run a single test by name
pytest tests/test_volume.py::test_buried_volume_is_positive_for_atom_at_origin

# Run the CLI
stericrender complex.xyz --center 1 --axis 2,3 --exclude 1 --output-prefix results/complex

# Regenerate gallery images
python scripts/run_examples.py --with-overlay --output-dir examples/images/sambvca
```

## Architecture

StericRender computes steric maps and buried-volume (%VBur) figures for organometallic complexes. It wraps `xyzrender` for molecular rendering and composites a topographic overlay on top.

**Pipeline (CLI entry point: `cli.py:main`):**
1. `io.py` — load atoms/frames from XYZ (single or multi-frame) or any format supported by `xyzrender.load()`
2. `selectors.py` — parse 1-based atom index specs (`--center`, `--axis`, `--include`, `--exclude`, `--frames`) into 0-based indices
3. `orientation.py` — translate the center atom to the origin and rotate so the center→axis vector aligns with +z; optional dihedral roll for deterministic orientation
4. `volume.py` — voxelise a sphere at the origin and classify voxels as buried by atom radii → `BuriedVolumeResult` with global, quadrant, and hemisphere %VBur
5. `maps.py` — ray-scan from +z to find the first occupied z per x/y grid point → `StericMapResult` (a 2-D topographic grid)
6. `export.py` — write `.json`, `_grid.csv`, `_grid.npz`, and `_map.svg`
7. `overlay.py` — call `xyzrender.render()` on the oriented XYZ, then insert the steric-map layer as SVG before `</svg>`

**Key design constraints:**
- All atom indices in the public API (CLI, JSON output) are **1-based**; internally everything uses **0-based** indices.
- `orientation.py` expects positions already translated so the center is at the origin; this is always done inside `orient_positions`.
- The overlay SVG coordinate system matches xyzrender's orthographic projection: x right, y up, z ignored. The `scale` factor is derived from `(canvas_size − 2·padding) / fixed_span`.
- `compute_steric_map` and `compute_buried_volume` accept positions already centred at the origin (post-orientation), not raw molecular coordinates.
- `radii.py` provides three atom-radius sets: `scaled-bondi` (default, 1.17× Bondi), `bondi`, and `csd`.

**Module responsibilities at a glance:**

| Module | Responsibility |
|---|---|
| `io.py` | XYZ I/O, `Atom`/`StructureFrame` dataclasses |
| `selectors.py` | Index spec parsing (`1,4-6`, `all`) |
| `orientation.py` | Rigid rotation to StericRender convention |
| `volume.py` | Voxel-based %VBur, quadrant/hemisphere breakdown |
| `maps.py` | 2-D topographic z-map grid |
| `visual.py` | SVG rendering primitives (colourbar, contours, palette) |
| `overlay.py` | Composite steric map onto xyzrender molecule SVG |
| `export.py` | File writers (JSON, CSV, NPZ, standalone map SVG) |
| `radii.py` | Atomic radius lookup tables |
| `validation.py` | Optional morfeus-ml cross-checks |

**Tests:**
- `test_volume.py` / `test_orientation.py` / `test_multi_xyz.py` — unit tests, no filesystem dependencies
- `test_sambvca_examples.py` — optional numeric regression against published %VBur values (requires `validation` extra)
- `test_visual.py` / `test_validation.py` — visual/SVG output checks
