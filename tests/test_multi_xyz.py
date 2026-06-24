import json
import subprocess
import sys
from pathlib import Path

from stericrender import cli
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
        "examples/sambvca/om6b00371_si_002.xyz",
        "--frames",
        "13,15",
        "--origin",
        "2",
        "--toward",
        "3,13,14,25",
        "--exclude",
        "1,65",
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
    summary_data = json.loads(summary.read_text())
    assert len(summary_data["frames"]) == 2
    assert "mean_percent_buried" in summary_data


def test_cli_overlay_defaults_to_selected_atoms(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    captured = {}

    def fake_overlay_renderer(**kwargs):
        overlay_xyz = Path(kwargs["oriented_xyz"])
        captured["overlay_xyz_name"] = overlay_xyz.name
        captured["overlay_xyz_text"] = overlay_xyz.read_text()
        captured["include_hydrogens"] = kwargs["include_hydrogens"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert captured["overlay_xyz_name"] == "simple_overlay_atoms.xyz"
    assert captured["overlay_xyz_text"].splitlines()[0] == "4"
    assert "Pd" not in captured["overlay_xyz_text"]
    assert captured["overlay_xyz_text"].count("\nP  ") == 1
    assert captured["overlay_xyz_text"].count("\nC  ") == 3
    assert captured["include_hydrogens"] is False
    assert not (tmp_path / "simple_overlay_atoms.xyz").exists()


def test_cli_sphere_and_map_radius_passed_to_overlay(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    captured = {}

    def fake_overlay_renderer(**kwargs):
        captured["sphere_radius"] = kwargs["sphere_radius"]
        captured["zoom"] = kwargs["zoom"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--sphere-radius",
            "7.0",
            "--zoom",
            "1.75",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    metadata = json.loads(output_prefix.with_suffix(".json").read_text())["metadata"]
    assert captured == {"sphere_radius": 7.0, "zoom": 1.75}
    assert metadata["sphere_radius"] == 7.0
    assert metadata["map_radius"] == 7.0
    assert metadata["zoom"] == 1.75


def test_cli_map_radius_independent_of_sphere_radius(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    captured = {}

    def fake_overlay_renderer(**kwargs):
        captured["sphere_radius"] = kwargs["sphere_radius"]
        captured["map_radius"] = kwargs["map_radius"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--sphere-radius",
            "3.5",
            "--map-radius",
            "5.0",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    metadata = json.loads(output_prefix.with_suffix(".json").read_text())["metadata"]
    # sphere_radius controls the circle and map; map_radius only widens the viewport
    assert captured["sphere_radius"] == 3.5
    assert captured["map_radius"] == 5.0
    assert metadata["sphere_radius"] == 3.5
    assert metadata["map_radius"] == 5.0


def test_cli_stereo_options_pass_to_overlay(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    captured = {}

    def fake_overlay_renderer(**kwargs):
        captured["stereo"] = kwargs["stereo"]
        captured["stereo_style"] = kwargs["stereo_style"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--stereo",
            "point,ez",
            "--stereo-style",
            "label",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    metadata = json.loads(output_prefix.with_suffix(".json").read_text())["metadata"]
    assert captured == {"stereo": ["point", "ez"], "stereo_style": "label"}
    assert metadata["stereo"] == "point,ez"
    assert metadata["stereo_style"] == "label"


def test_cli_can_hide_overlay_vbur_label(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    captured = {}

    def fake_overlay_renderer(**kwargs):
        captured["show_vbur_label"] = kwargs["show_vbur_label"]
        captured["show_colorbar"] = kwargs["show_colorbar"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--no-vbur-label",
            "--no-colorbar",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    metadata = json.loads(output_prefix.with_suffix(".json").read_text())["metadata"]
    assert captured == {"show_vbur_label": False, "show_colorbar": False}
    assert metadata["show_vbur_label"] is False


def test_cli_accepts_legacy_map_subcommand(tmp_path):
    output_prefix = tmp_path / "legacy"

    cli.main(
        [
            "map",
            "examples/simple.xyz",
            "--origin",
            "1",
            "--toward",
            "2",
            "--no-overlay",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert output_prefix.with_suffix(".json").is_file()


def test_cli_include_hydrogens_passes_hydrogens_to_overlay(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    input_xyz = tmp_path / "with_h.xyz"
    input_xyz.write_text(
        "\n".join(
            [
                "6",
                "hydrogen overlay fixture",
                "Pd 0.0 0.0 0.0",
                "P 0.0 0.0 2.2",
                "C 1.5 0.0 2.9",
                "H 2.1 0.0 3.4",
                "H 1.2 0.9 3.2",
                "H 1.2 -0.9 3.2",
                "",
            ]
        )
    )
    captured = {}

    def fake_overlay_renderer(**kwargs):
        overlay_xyz = Path(kwargs["oriented_xyz"])
        captured["overlay_xyz_text"] = overlay_xyz.read_text()
        captured["include_hydrogens"] = kwargs["include_hydrogens"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            str(input_xyz),
            "--origin",
            "1",
            "--toward",
            "2",
            "--include-hydrogens",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert captured["include_hydrogens"] is True
    assert captured["overlay_xyz_text"].splitlines()[0] == "5"
    assert captured["overlay_xyz_text"].count("\nH  ") == 3


def test_cli_keeps_hidden_hydrogens_for_overlay_bond_order_context(tmp_path, monkeypatch):
    output_prefix = tmp_path / "simple"
    input_xyz = tmp_path / "with_h.xyz"
    input_xyz.write_text(
        "\n".join(
            [
                "6",
                "hidden hydrogen graph fixture",
                "Pd 0.0 0.0 0.0",
                "P 0.0 0.0 2.2",
                "C 1.5 0.0 2.9",
                "H 2.1 0.0 3.4",
                "H 1.2 0.9 3.2",
                "H 1.2 -0.9 3.2",
                "",
            ]
        )
    )
    captured = {}

    def fake_overlay_renderer(**kwargs):
        overlay_xyz = Path(kwargs["oriented_xyz"])
        captured["overlay_xyz_text"] = overlay_xyz.read_text()
        captured["include_hydrogens"] = kwargs["include_hydrogens"]

    monkeypatch.setattr(cli, "write_xyzrender_overlay_svg", fake_overlay_renderer)

    cli.main(
        [
            str(input_xyz),
            "--origin",
            "1",
            "--toward",
            "2",
            "--output-prefix",
            str(output_prefix),
        ]
    )

    metadata = json.loads(output_prefix.with_suffix(".json").read_text())["metadata"]
    assert captured["include_hydrogens"] is False
    assert captured["overlay_xyz_text"].splitlines()[0] == "5"
    assert captured["overlay_xyz_text"].count("\nH  ") == 3
    assert metadata["selected_atoms"] == [2, 3]
