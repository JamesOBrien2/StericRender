#!/usr/bin/env python
"""Run curated StericRender examples and compare against expected values."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from split_sambvca_si import split_multi_xyz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--si-xyz", default="examples/sambvca/om6b00371_si_002.xyz")
    parser.add_argument("--cases", default="examples/sambvca/cases.json")
    parser.add_argument("--structures-dir", default="examples/sambvca/structures")
    parser.add_argument("--output-dir", default="output/examples/sambvca")
    parser.add_argument("--with-overlay", action="store_true")
    parser.add_argument("--tolerance", type=float, default=0.25)
    args = parser.parse_args()

    structures = split_multi_xyz(Path(args.si_xyz), Path(args.structures_dir))
    cases = json.loads(Path(args.cases).read_text())
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for case in cases:
        structure_path = structures[case["structure_index"] - 1]
        prefix = output_dir / case["name"]
        command = [
            sys.executable,
            "-m",
            "stericrender.cli",
            "map",
            str(structure_path),
            "--center",
            case["center"],
            "--axis",
            case["axis"],
            "--exclude",
            case["exclude"],
            "--config",
            case.get("config", "flat"),
            "--color-range",
            str(case.get("color_min", -3)),
            str(case.get("color_max", 3)),
            "--output-prefix",
            str(prefix),
        ]
        if case.get("dihedral"):
            command.extend(["--dihedral", case["dihedral"]])
        if case.get("dihedral_target") is not None:
            command.extend(["--dihedral-target", str(case["dihedral_target"])])
        if case.get("flip_z"):
            command.append("--flip-z")
        if not args.with_overlay:
            command.append("--no-overlay")
        completed = subprocess.run(command, text=True, capture_output=True, check=True)
        data = json.loads(prefix.with_suffix(".json").read_text())
        actual = float(data["percent_buried"])
        expected = case.get("expected_percent_buried")
        delta = actual - float(expected) if expected is not None else None
        ok = abs(delta) <= args.tolerance if delta is not None else True
        results.append(
            {
                "name": case["name"],
                "figure": case.get("figure"),
                "actual": actual,
                "expected": expected,
                "delta": delta,
                "ok": ok,
                "validated": expected is not None,
                "stdout": completed.stdout.strip().splitlines(),
            }
        )
        if expected is None:
            print(f"{case['name']}: {actual:.2f} paper-oriented")
        else:
            print(f"{case['name']}: {actual:.2f} expected {float(expected):.2f} delta {delta:+.2f}")

    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    if not all(item["ok"] for item in results):
        raise SystemExit(f"One or more examples exceeded tolerance {args.tolerance}; see {report_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
