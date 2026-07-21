<p align="center"><img src="docs/logo.png" alt="StericRender" width="720"></p>

# StericRender: Topographic Steric Mapping with Molecular Visualisation

StericRender computes topographic steric maps and buried volume (%V*Bur*) for any molecular structure, producing publication-quality SVG figures from the command line. It implements the SambVca methodology and uses [`xyzrender`](https://github.com/aligfellow/xyzrender) for oriented molecular overlays.

[![PyPI](https://img.shields.io/pypi/v/stericrender)](https://pypi.org/project/stericrender/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://pypi.org/project/stericrender/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/JamesOBrien2/StericRender/blob/main/LICENSE)
[![Powered by: uv](https://img.shields.io/badge/-uv-purple)](https://docs.astral.sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Typing: ty](https://img.shields.io/badge/typing-ty-EFC621.svg)](https://github.com/astral-sh/ty)
[![CI](https://github.com/JamesOBrien2/StericRender/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JamesOBrien2/StericRender/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/JamesOBrien2/StericRender/branch/main/graph/badge.svg)](https://codecov.io/gh/JamesOBrien2/StericRender)


![zoomed out overlay](examples/images/controls/zoom_overlay.svg)

## What it produces

- Topographic steric maps (SVG, CSV, NPZ)
- Buried volume (%VBur) with quadrant breakdowns (JSON)
- Oriented molecular overlay SVG via xyzrender
- Multi-frame XYZ batch processing
- Three atomic radii sets: scaled-Bondi (default), Bondi, CSD
- Configurable sphere radius, map radius, mesh spacing, colour palettes

## CLI

```bash
stericrender complex.xyz \
  --origin 1 \
  --toward 2,3 \
  --flip-z \
  --config pmol \
  --overlay-opacity 0.72 \
  --map-palette sambvca \
  --color-range -3 3 \
  --output-prefix results/complex
```

The origin atom is automatically excluded from the steric analysis. Use `--include-origin` to override.

## Installation

```bash
pip install stericrender
# latest development version:
pip install --upgrade git+https://github.com/JamesOBrien2/StericRender.git
```

Or with uv:

```bash
uv tool install stericrender
```

From source:

```bash
git clone https://github.com/JamesOBrien2/StericRender.git
cd StericRender
pip install -e .
```

## Python API

```python
import numpy as np
from stericrender.io import load_structure_frames, atoms_to_arrays
from stericrender.orientation import orient_positions
from stericrender.radii import radii_for_symbols
from stericrender import compute_buried_volume, compute_steric_map

frames = load_structure_frames("complex.xyz")
symbols, positions = atoms_to_arrays(frames[0].atoms)

# orient: atom 1 at origin, +z toward atom 2
oriented = orient_positions(positions, center_index=0, axis_indices=[1])
selected = [i for i, s in enumerate(symbols) if s != "H" and i != 0]
radii = np.array(radii_for_symbols([symbols[i] for i in selected]))

volume = compute_buried_volume(oriented.positions[selected], radii)
print(f"%VBur = {volume.percent_buried:.2f}")

steric_map = compute_steric_map(oriented.positions[selected], radii)
# steric_map.x, steric_map.y, steric_map.z — topographic grid arrays
```

## Sphere radius and map radius

`--sphere-radius` scales the analysis sphere; `--map-radius` sets the display extent independently.

| `--sphere-radius 2` | `--map-radius 5` |
| ------------------- | ---------------- |
| ![larger steric radius](examples/images/controls/radius_overlay.svg) | ![zoomed out overlay](examples/images/controls/zoom_overlay.svg) |

### Available flags

`--include`, `--exclude`, `--include-origin`, `--frames`, `--radii`, `--include-hydrogens`, `--sphere-radius`, `--map-radius`, `--mesh`, `--config`, `--overlay-opacity`, `--overlay-all-atoms`, `--zoom`, `--stereo`, `--stereo-style`, `--no-contours`, `--no-colorbar`, `--no-vbur-label`, `--show-quadrants`, `--no-overlay`

## Gallery

### Monocoordinated Ligands

| PCy3                                                              | NHC-Ni                                                              | NHC-Ir                                                              |
| ----------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| ![complex 1](examples/images/sambvca/complex_01_pcy3_overlay.svg) | ![complex 2](examples/images/sambvca/complex_02_nhc_ni_overlay.svg) | ![complex 3](examples/images/sambvca/complex_03_nhc_ir_overlay.svg) |

### Dicoordinated Ligands

| MeDuPhos                                                              | Box                                                              | Diphosphine                                                              |
| --------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ![complex 4](examples/images/sambvca/complex_04_meduphos_overlay.svg) | ![complex 5](examples/images/sambvca/complex_05_box_overlay.svg) | ![complex 6](examples/images/sambvca/complex_06_diphosphine_overlay.svg) |

| PHOX                                                              | Xantphos                                                              | Diimine                                                              |
| ----------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| ![complex 7](examples/images/sambvca/complex_07_phox_overlay.svg) | ![complex 8](examples/images/sambvca/complex_08_xantphos_overlay.svg) | ![complex 9](examples/images/sambvca/complex_09_diimine_overlay.svg) |

| TADDOL                                                               | BINOL                                                               | Bipy                                                               |
| -------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| ![complex 10](examples/images/sambvca/complex_10_taddol_overlay.svg) | ![complex 11](examples/images/sambvca/complex_11_binol_overlay.svg) | ![complex 12](examples/images/sambvca/complex_12_bipy_overlay.svg) |

### Tetracoordinated Ligands

| Salen-Mn                                                               | Chiral salen-Mn                                                               | Zr-ONNO                                                                  |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ![complex 13](examples/images/sambvca/complex_13_salen_mn_overlay.svg) | ![complex 14](examples/images/sambvca/complex_14_chiral_salen_mn_overlay.svg) | ![complex 15](examples/images/sambvca/complex_15_zr_complex_overlay.svg) |

### Zirconocenes

| C2 zirconocene                                                               | Substituted zirconocene                                                               | Cs zirconocene                                                               |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ![complex 16](examples/images/sambvca/complex_16_c2_zirconocene_overlay.svg) | ![complex 17](examples/images/sambvca/complex_17_substituted_zirconocene_overlay.svg) | ![complex 18](examples/images/sambvca/complex_18_cs_zirconocene_overlay.svg) |

## Acknowledgements

- The [SambVca](https://www.icb.csic.es/sambvca2-0/) group (Cavallo et al.) — the %VBur methodology and topographic steric map convention that StericRender implements
- [morfeus-ml](https://github.com/digital-chemistry-laboratory/morfeus) — reference implementation used for validation
- [xyzrender](https://github.com/aligfellow/xyzrender) by [@aligfellow](https://github.com/aligfellow) — molecular rendering and SVG overlay
- [Jonathan Di Pietro (@jonathandip)](https://github.com/jonathandip) — zoom and radius concept, testing


## Citation

If you use StericRender in published research, cite the software version used:

> James O'Brien, *StericRender: Topographic Steric Mapping with Molecular
> Visualisation*, version 1.1.0, computer software, Zenodo, 2026,
> https://doi.org/10.5281/zenodo.21474975

Machine-readable citation metadata is available in [`CITATION.cff`](CITATION.cff).
GitHub also provides APA and BibTeX entries through the **Cite this repository**
menu. Cite the version-specific Zenodo DOI so that the exact software used can
be recovered.

Please also cite the methodological works on which StericRender builds:

1. Laura Falivene, Raffaele Credendino, Albert Poater, Andrea Petta, Luigi Serra, Romina Oliva, Vittorio Scarano, and Luigi Cavallo,  
   "SambVca 2. A Web Tool for Analyzing Catalytic Pockets with Topographic Steric Maps,"  
   *Organometallics* **2016**, *35*, 2286–2293.  
   DOI: [`10.1021/acs.organomet.6b00371`](https://doi.org/10.1021/acs.organomet.6b00371)

2. Sílvia Escayola, Naeimeh Bahri-Laleh, and Albert Poater,  
   "%VBur index and steric maps: from predictive catalysis to machine learning,"  
   *Chemical Society Reviews* **2024**, *53*, 853–882.  
   DOI: [`10.1039/D3CS00725A`](https://doi.org/10.1039/D3CS00725A)

3. A. S. Goodfellow and B. N. Nguyen,  
   "Graph-Based Internal Coordinate Analysis for Transition State Characterization",
   *Journal of Chemical Theory and Computation* **2026**.  
   DOI: [`10.1021/acs.jctc.5c02073`](https://doi.org/10.1021/acs.jctc.5c02073)
