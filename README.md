<p align="center">
  <img src="StericRender_colour.svg" alt="StericRender" width="720">
</p>

___

Steric maps and buried-volume figures, oriented with `xyzrender`.

| Overlay | Steric map |
|---|---|
| <img src="examples/images/sambvca/complex_04_meduphos_overlay.svg" alt="example overlay" width="224"> | <img src="examples/images/sambvca/complex_04_meduphos_map.svg" alt="example map" width="300"> |

## Gallery

All examples are generated from the ACS SambVca SI multi-XYZ file. `[ref]`
marks cases with a published `%VBur` value used as a numeric check.

```bash
python scripts/run_examples.py --with-overlay --output-dir examples/images/sambvca
```

### Monocoordinated Ligands

| PCy3 [ref] | NHC-Ni | NHC-Ir |
|---|---|---|
| ![complex 1](examples/images/sambvca/complex_01_pcy3_overlay.svg) | ![complex 2](examples/images/sambvca/complex_02_nhc_ni_overlay.svg) | ![complex 3](examples/images/sambvca/complex_03_nhc_ir_overlay.svg) |

### Dicoordinated Ligands

| MeDuPhos | Box [ref] | Diphosphine |
|---|---|---|
| ![complex 4](examples/images/sambvca/complex_04_meduphos_overlay.svg) | ![complex 5](examples/images/sambvca/complex_05_box_overlay.svg) | ![complex 6](examples/images/sambvca/complex_06_diphosphine_overlay.svg) |

| PHOX | Xantphos | Diimine |
|---|---|---|
| ![complex 7](examples/images/sambvca/complex_07_phox_overlay.svg) | ![complex 8](examples/images/sambvca/complex_08_xantphos_overlay.svg) | ![complex 9](examples/images/sambvca/complex_09_diimine_overlay.svg) |

| TADDOL | BINOL | Bipy |
|---|---|---|
| ![complex 10](examples/images/sambvca/complex_10_taddol_overlay.svg) | ![complex 11](examples/images/sambvca/complex_11_binol_overlay.svg) | ![complex 12](examples/images/sambvca/complex_12_bipy_overlay.svg) |

### Tetracoordinated Ligands

| Salen-Mn [ref] | Chiral salen-Mn [ref] | Zr-ONNO [ref] |
|---|---|---|
| ![complex 13](examples/images/sambvca/complex_13_salen_mn_overlay.svg) | ![complex 14](examples/images/sambvca/complex_14_chiral_salen_mn_overlay.svg) | ![complex 15](examples/images/sambvca/complex_15_zr_complex_overlay.svg) |

### Zirconocenes

| C2 zirconocene | Substituted zirconocene | Cs zirconocene |
|---|---|---|
| ![complex 16](examples/images/sambvca/complex_16_c2_zirconocene_overlay.svg) | ![complex 17](examples/images/sambvca/complex_17_substituted_zirconocene_overlay.svg) | ![complex 18](examples/images/sambvca/complex_18_cs_zirconocene_overlay.svg) |

## CLI

```bash
stericrender map complex.xyz \
  --center 1 \
  --axis 2,3 \
  --exclude 1 \
  --flip-z \
  --config flat \
  --overlay-opacity 0.72 \
  --map-palette sambvca \
  --color-range -3 3 \
  --output-prefix results/complex
```

Radius and zoom examples:

```bash
# Increase the analytical steric-map sphere radius.
stericrender map complex.xyz --center 1 --axis 2,3 --exclude 1 --radius 4.5

# Zoom the overlay out while keeping the steric-map radius unchanged.
stericrender map complex.xyz --center 1 --axis 2,3 --exclude 1 --zoom 1.6

# Combine a larger steric-map radius with a wider overlay view.
stericrender map complex.xyz --center 1 --axis 2,3 --exclude 1 --radius 4.5 --zoom 1.6
```

Outputs:

```text
results/complex.json
results/complex_grid.csv
results/complex_grid.npz
results/complex_map.svg
results/complex_overlay.svg
results/complex_oriented.xyz
```

Useful flags: `--include`, `--exclude`, `--frames`, `--radii`,
`--include-hydrogens`, `--sphere-radius`/`--radius`, `--mesh`, `--visual-mesh`,
`--config`, `--overlay-opacity`, `--overlay-all-atoms`, `--zoom`,
`--no-contours`, `--no-colorbar`, `--show-quadrants`, `--no-overlay`.
