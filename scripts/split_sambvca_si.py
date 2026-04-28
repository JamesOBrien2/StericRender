#!/usr/bin/env python
"""Split the SambVca supporting-information multi-XYZ into per-complex files."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="examples/sambvca/om6b00371_si_002.xyz")
    parser.add_argument("--output-dir", default="examples/sambvca/structures")
    args = parser.parse_args()
    paths = split_multi_xyz(Path(args.input), Path(args.output_dir))
    for path in paths:
        print(path)


def split_multi_xyz(input_path: Path, output_dir: Path) -> list[Path]:
    lines = input_path.read_text(errors="replace").splitlines()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    i = 0
    structure_index = 0
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
        structure_index += 1
        chunk = lines[i : i + n_atoms + 2]
        output_path = output_dir / f"complex_{structure_index:02d}.xyz"
        output_path.write_text("\n".join(chunk) + "\n")
        paths.append(output_path)
        i += n_atoms + 2
    return paths


if __name__ == "__main__":
    main()

