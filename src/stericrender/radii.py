"""Atomic radius tables for buried-volume calculations."""

from __future__ import annotations

BONDI_RADII = {
    "H": 1.20,
    "B": 1.92,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "F": 1.47,
    "Si": 2.10,
    "P": 1.80,
    "S": 1.80,
    "Cl": 1.75,
    "Br": 1.85,
    "I": 1.98,
}

CSD_RADII = {
    "H": 1.09,
    "B": 1.92,
    "C": 1.77,
    "N": 1.64,
    "O": 1.58,
    "F": 1.46,
    "Si": 2.10,
    "P": 1.90,
    "S": 1.81,
    "Cl": 1.82,
    "Br": 1.86,
    "I": 2.04,
}


def radius_for_symbol(symbol: str, radii: str = "scaled-bondi", default: float = 2.0) -> float:
    """Return a van der Waals radius for an element symbol."""
    normalized = symbol.strip().capitalize()
    if radii == "bondi":
        return BONDI_RADII.get(normalized, default)
    if radii == "scaled-bondi":
        return BONDI_RADII.get(normalized, default) * 1.17
    if radii == "csd":
        return CSD_RADII.get(normalized, default * 1.17)
    raise ValueError(f"Unknown radii set: {radii}")


def radii_for_symbols(symbols: list[str], radii: str = "scaled-bondi") -> list[float]:
    """Return radii for symbols."""
    return [radius_for_symbol(symbol, radii=radii) for symbol in symbols]
