"""Input and output helpers for StericRender."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Atom:
    """Minimal atom record used by the steric core."""

    symbol: str
    position: np.ndarray
    index: int


@dataclass(frozen=True)
class StructureFrame:
    """One molecular structure from an input file."""

    atoms: list[Atom]
    title: str
    index: int


def load_atoms(path: str | Path) -> list[Atom]:
    """Load atoms using xyzrender when available, falling back to simple XYZ."""
    input_path = Path(path)
    try:
        from xyzrender import load

        mol = load(input_path)
        atoms: list[Atom] = []
        for i, node in enumerate(sorted(mol.graph.nodes())):
            data = mol.graph.nodes[node]
            atoms.append(
                Atom(
                    symbol=str(data["symbol"]),
                    position=np.array(data["position"], dtype=float),
                    index=i + 1,
                )
            )
        return atoms
    except ModuleNotFoundError:
        return load_xyz_atoms(input_path)


def load_structure_frames(path: str | Path) -> list[StructureFrame]:
    """Load one or more structures.

    Multi-XYZ files are returned as multiple frames. Other formats are delegated
    to ``xyzrender.load``/``load_atoms`` and returned as a single frame.
    """
    input_path = Path(path)
    if input_path.suffix.lower() == ".xyz":
        frames = load_xyz_frames(input_path)
        if frames:
            return frames
    return [StructureFrame(load_atoms(input_path), input_path.stem, 1)]


def load_xyz_atoms(path: str | Path) -> list[Atom]:
    """Load a plain XYZ file."""
    frames = load_xyz_frames(path)
    if not frames:
        raise ValueError(f"No XYZ frames found in {path}")
    return frames[0].atoms


def load_xyz_frames(path: str | Path) -> list[StructureFrame]:
    """Load all frames from a plain or multi-frame XYZ file."""
    input_path = Path(path)
    lines = input_path.read_text().splitlines()
    if len(lines) < 2:
        raise ValueError(f"Not enough lines for XYZ input: {input_path}")
    frames: list[StructureFrame] = []
    cursor = 0
    while cursor < len(lines):
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            break
        try:
            n_atoms = int(lines[cursor].strip())
        except ValueError as exc:
            if not frames:
                raise ValueError(f"First XYZ frame line must be atom count: {input_path}") from exc
            raise ValueError(f"Invalid XYZ atom count at line {cursor + 1}: {lines[cursor]!r}") from exc
        title = lines[cursor + 1].strip() if cursor + 1 < len(lines) else ""
        atom_lines = lines[cursor + 2 : cursor + 2 + n_atoms]
        atoms: list[Atom] = []
        for idx, line in enumerate(atom_lines, start=1):
            parts = line.split()
            if len(parts) < 4:
                raise ValueError(f"Invalid XYZ atom line {idx} in frame {len(frames) + 1}: {line!r}")
            atoms.append(Atom(parts[0], np.array([float(parts[1]), float(parts[2]), float(parts[3])]), idx))
        if len(atoms) != n_atoms:
            raise ValueError(f"XYZ frame {len(frames) + 1} declared {n_atoms} atoms but provided {len(atoms)}")
        frames.append(StructureFrame(atoms, title, len(frames) + 1))
        cursor += n_atoms + 2
    return frames


def write_xyz(atoms: list[Atom], path: str | Path, title: str = "") -> None:
    """Write atoms to XYZ."""
    output_path = Path(path)
    lines = [f"{len(atoms)}\n", f"{title}\n"]
    for atom in atoms:
        x, y, z = atom.position
        lines.append(f"{atom.symbol:<3} {x:15.8f} {y:15.8f} {z:15.8f}\n")
    output_path.write_text("".join(lines))


def atoms_to_arrays(atoms: list[Atom]) -> tuple[list[str], np.ndarray]:
    """Return parallel symbol and position arrays."""
    return [atom.symbol for atom in atoms], np.array([atom.position for atom in atoms], dtype=float)


def arrays_to_atoms(symbols: list[str], positions: np.ndarray) -> list[Atom]:
    """Build atom records from symbols and positions."""
    return [Atom(symbol, np.array(pos, dtype=float), i + 1) for i, (symbol, pos) in enumerate(zip(symbols, positions))]
