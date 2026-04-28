# SambVca SI Examples

`om6b00371_si_002.xyz` contains complexes 1-18 from the SambVca 2
supporting information.

```bash
python scripts/run_examples.py --with-overlay --output-dir examples/images/sambvca
```

`cases.json` stores the atom-index orientation, excluded atoms, and optional
published `%VBur` targets. Cases without a target are included as
paper-oriented gallery examples.
