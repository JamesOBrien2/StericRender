<p align="center">
  <img src="StericRender_colour.svg" alt="StericRender" width="720">
</p>

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

### Figure 5: Monocoordinated Ligands

| 1 PCy3, 29.61 [ref] | 2 NHC-Ni, 36.12 | 3 NHC-Ir, 43.90 |
|---|---|---|
| ![complex 1](examples/images/sambvca/complex_01_pcy3_overlay.svg) | ![complex 2](examples/images/sambvca/complex_02_nhc_ni_overlay.svg) | ![complex 3](examples/images/sambvca/complex_03_nhc_ir_overlay.svg) |

### Figure 6: Dicoordinated Ligands

| 4 MeDuPhos, 46.90 [ref] | 5 Box, 43.80 [ref] | 6 Diphosphine, 53.84 |
|---|---|---|
| ![complex 4](examples/images/sambvca/complex_04_meduphos_overlay.svg) | ![complex 5](examples/images/sambvca/complex_05_box_overlay.svg) | ![complex 6](examples/images/sambvca/complex_06_diphosphine_overlay.svg) |

| 7 PHOX, 49.10 | 8 Xantphos, 52.68 | 9 Diimine, 47.73 |
|---|---|---|
| ![complex 7](examples/images/sambvca/complex_07_phox_overlay.svg) | ![complex 8](examples/images/sambvca/complex_08_xantphos_overlay.svg) | ![complex 9](examples/images/sambvca/complex_09_diimine_overlay.svg) |

| 10 TADDOL, 40.14 | 11 BINOL, 35.86 | 12 Bipy, 36.12 |
|---|---|---|
| ![complex 10](examples/images/sambvca/complex_10_taddol_overlay.svg) | ![complex 11](examples/images/sambvca/complex_11_binol_overlay.svg) | ![complex 12](examples/images/sambvca/complex_12_bipy_overlay.svg) |

### Figure 7: Tetracoordinated Ligands

| 13 Salen-Mn, 64.17 [ref] | 14 Chiral salen-Mn, 65.38 [ref] | 15 Zr-ONNO, 60.40 [ref] |
|---|---|---|
| ![complex 13](examples/images/sambvca/complex_13_salen_mn_overlay.svg) | ![complex 14](examples/images/sambvca/complex_14_chiral_salen_mn_overlay.svg) | ![complex 15](examples/images/sambvca/complex_15_zr_complex_overlay.svg) |

### Figure 8: Zirconocenes

| 16 C2 zirconocene, 64.84 | 17 Substituted zirconocene, 66.71 | 18 Cs zirconocene, 63.98 |
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
`--include-hydrogens`, `--sphere-radius`, `--mesh`, `--visual-mesh`,
`--config`, `--overlay-opacity`, `--overlay-all-atoms`,
`--no-contours`, `--no-colorbar`, `--show-quadrants`, `--no-overlay`.
