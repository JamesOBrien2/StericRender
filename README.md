<p align="center">
  <img src="examples/logo/logo.svg" alt="StericRender" width="520">
</p>

---

**StericRender** applies the concepts and methods from steric maps and buried-volume analysis ([`SambVca`](https://pubs.acs.org/doi/10.1021/acs.organomet.6b00371)), with the molecular rendering workflow [`xyzrender`](https://github.com/aligfellow/xyzrender).


### Radius/Zoom

`--radius` scales the steric-map sphere; `--zoom` only changes the overlay framing.

| `--radius 2`                                                         | `--zoom 1.6`                                                     |
| -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| ![larger steric radius](examples/images/controls/radius_overlay.svg) | ![zoomed out overlay](examples/images/controls/zoom_overlay.svg) |

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

## CLI Arguments

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

#### Available flags
`--include`, `--exclude`, `--frames`, `--radii`,
`--include-hydrogens`, `--sphere-radius`/`--radius`, `--mesh`, `--visual-mesh`,
`--config`, `--overlay-opacity`, `--overlay-all-atoms`, `--zoom`,
`--stereo`, `--stereo-style`, `--no-contours`, `--no-colorbar`,
`--no-vbur-label`, `--show-quadrants`, `--no-overlay`.

## References

If you use this repository, you must cite the following works:

1. Laura Falivene, Raffaele Credendino, Albert Poater, Andrea Petta, Luigi Serra, Romina Oliva, Vittorio Scarano, and Luigi Cavallo,  
   “SambVca 2. A Web Tool for Analyzing Catalytic Pockets with Topographic Steric Maps,”  
   *Organometallics* **2016**, *35*, 2286–2293.  
   DOI: [`10.1021/acs.organomet.6b00371`](https://doi.org/10.1021/acs.organomet.6b00371)

2. Sílvia Escayola, Naeimeh Bahri-Laleh, and Albert Poater,  
   “%VBur index and steric maps: from predictive catalysis to machine learning,”  
   *Chemical Society Reviews* **2024**, *53*, 853–882.

3. A. S. Goodfellow and B. N. Nguyen,  
   “xyzrender,”  
   *Journal of Chemical Theory and Computation* **2026**.  
   DOI: [`10.1021/acs.jctc.5c02073`](https://doi.org/10.1021/acs.jctc.5c02073)
