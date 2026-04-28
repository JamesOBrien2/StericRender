import json
import subprocess
import sys
from pathlib import Path

from stericrender.io import load_xyz_frames


def test_load_xyz_frames_reads_multi_xyz():
    frames = load_xyz_frames("examples/sambvca/om6b00371_si_002.xyz")
    assert len(frames) == 18
    assert frames[0].index == 1
    assert frames[0].title.startswith("complex 1")
    assert len(frames[12].atoms) == 65


def test_cli_multi_xyz_selected_frames(tmp_path):
    output_prefix = tmp_path / "multi"
    command = [
        sys.executable,
        "-m",
        "stericrender.cli",
        "map",
        "examples/sambvca/om6b00371_si_002.xyz",
        "--frames",
        "13,15",
        "--center",
        "2",
        "--axis",
        "3,13,14,25",
        "--exclude",
        "1,2,65",
        "--no-overlay",
        "--output-prefix",
        str(output_prefix),
    ]
    subprocess.run(command, check=True)
    frame_13 = output_prefix.parent / "multi_frame_013.json"
    frame_15 = output_prefix.parent / "multi_frame_015.json"
    summary = output_prefix.parent / "multi_summary.json"
    assert frame_13.is_file()
    assert frame_15.is_file()
    assert summary.is_file()
    assert json.loads(frame_13.read_text())["metadata"]["frame"] == 13
    assert len(json.loads(summary.read_text())) == 2
