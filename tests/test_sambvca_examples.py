import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_curated_sambvca_examples_match_reference_values(tmp_path):
    si_path = Path("examples/sambvca/om6b00371_si_002.xyz")
    if not si_path.is_file():
        pytest.skip("SambVca SI XYZ not present")
    output_dir = tmp_path / "examples"
    command = [
        sys.executable,
        "scripts/run_examples.py",
        "--output-dir",
        str(output_dir),
        "--tolerance",
        "0.25",
    ]
    subprocess.run(command, check=True)
    report = json.loads((output_dir / "report.json").read_text())
    assert len(report) == 18
    assert all(item["ok"] for item in report)
    assert {item["name"] for item in report} >= {
        "complex_04_meduphos",
        "complex_05_box",
        "complex_13_salen_mn",
        "complex_14_chiral_salen_mn",
        "complex_15_zr_complex",
    }
    assert sum(1 for item in report if item["validated"]) >= 6
