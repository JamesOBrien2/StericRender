<p align="center">
  <img src="examples/logo/logo.svg" alt="StericRender" width="520">
</p>

---

Steric maps and buried-volume figures with molecular visualisations rendered with [`xyzrender`](https://github.com/aligfellow/xyzrender).

### Monocoordinated Ligands

| PCy3 [ref]                                                        | NHC-Ni                                                              | NHC-Ir                                                              |
| ----------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| ![complex 1](examples/images/sambvca/complex_01_pcy3_overlay.svg) | ![complex 2](examples/images/sambvca/complex_02_nhc_ni_overlay.svg) | ![complex 3](examples/images/sambvca/complex_03_nhc_ir_overlay.svg) |

### Dicoordinated Ligands

| MeDuPhos                                                              | Box [ref]                                                        | Diphosphine                                                              |
| --------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ![complex 4](examples/images/sambvca/complex_04_meduphos_overlay.svg) | ![complex 5](examples/images/sambvca/complex_05_box_overlay.svg) | ![complex 6](examples/images/sambvca/complex_06_diphosphine_overlay.svg) |

| PHOX                                                              | Xantphos                                                              | Diimine                                                              |
| ----------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| ![complex 7](examples/images/sambvca/complex_07_phox_overlay.svg) | ![complex 8](examples/images/sambvca/complex_08_xantphos_overlay.svg) | ![complex 9](examples/images/sambvca/complex_09_diimine_overlay.svg) |

| TADDOL                                                               | BINOL                                                               | Bipy                                                               |
| -------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| ![complex 10](examples/images/sambvca/complex_10_taddol_overlay.svg) | ![complex 11](examples/images/sambvca/complex_11_binol_overlay.svg) | ![complex 12](examples/images/sambvca/complex_12_bipy_overlay.svg) |

### Tetracoordinated Ligands

| Salen-Mn [ref]                                                         | Chiral salen-Mn [ref]                                                         | Zr-ONNO [ref]                                                            |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ![complex 13](examples/images/sambvca/complex_13_salen_mn_overlay.svg) | ![complex 14](examples/images/sambvca/complex_14_chiral_salen_mn_overlay.svg) | ![complex 15](examples/images/sambvca/complex_15_zr_complex_overlay.svg) |

### Zirconocenes

| C2 zirconocene                                                               | Substituted zirconocene                                                               | Cs zirconocene                                                               |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ![complex 16](examples/images/sambvca/complex_16_c2_zirconocene_overlay.svg) | ![complex 17](examples/images/sambvca/complex_17_substituted_zirconocene_overlay.svg) | ![complex 18](examples/images/sambvca/complex_18_cs_zirconocene_overlay.svg) |

## CLI

```bash
stericrender complex.xyz \
  --center 1 \
  --axis 2,3 \
  --exclude 1 \
  --flip-z \
  --config pmol \
  --overlay-opacity 0.72 \
  --map-palette sambvca \
  --color-range -3 3 \
  --output-prefix results/complex
```

Radius and zoom examples:

`--radius` scales the steric-map sphere; `--zoom` only changes the overlay framing.

| `--radius 2`                                                         | `--zoom 1.6`                                                     |
| -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| ![larger steric radius](examples/images/controls/radius_overlay.svg) | ![zoomed out overlay](examples/images/controls/zoom_overlay.svg) |

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
`--stereo`, `--stereo-style`, `--no-contours`, `--no-colorbar`,
`--no-vbur-label`, `--show-quadrants`, `--no-overlay`.
