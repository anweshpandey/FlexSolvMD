"""Composition calculations for water-DMSO mixtures.

This module calculates integer molecule counts for a binary mixture.
It does not build coordinates or validate force-field compatibility.
"""

from dataclasses import dataclass
from math import isclose


# Molar masses in grams per mole
MOLAR_MASS = {
    "water": 18.01528,
    "dmso": 78.13,
}


@dataclass(frozen=True)
class MixtureComposition:
    """Requested and achieved composition of a water-DMSO mixture."""

    water_molecules: int
    dmso_molecules: int
    requested_fraction: float
    fraction_type: str
    achieved_mole_fraction_dmso: float
    achieved_mass_fraction_dmso: float


def calculate_from_mole_fraction(
    dmso_mole_fraction: float,
    total_molecules: int,
) -> MixtureComposition:
    """Calculate molecule counts from the requested DMSO mole fraction.

    Args:
        dmso_mole_fraction: DMSO mole fraction, between 0 and 1.
        total_molecules: Total number of water and DMSO molecules.

    Returns:
        A MixtureComposition containing integer counts and achieved
        mole and mass fractions.
    """
    _validate_fraction(dmso_mole_fraction)

    if not isinstance(total_molecules, int) or isinstance(
        total_molecules, bool
    ):
        raise ValueError("total_molecules must be a positive integer.")

    if total_molecules <= 0:
        raise ValueError("total_molecules must be greater than zero.")

    dmso_count = round(total_molecules * dmso_mole_fraction)
    water_count = total_molecules - dmso_count

    return _build_result(
        water_count,
        dmso_count,
        dmso_mole_fraction,
        "mole_fraction",
    )


def calculate_from_mass_fraction(
    dmso_mass_fraction: float,
    total_molecules: int,
) -> MixtureComposition:
    """Calculate molecule counts from the requested DMSO mass fraction.

    The requested mass fraction is converted to a mole fraction using
    the molecular masses. Integer counts are then chosen to approximate
    the target composition as closely as possible.
    """
    _validate_fraction(dmso_mass_fraction)

    if not isinstance(total_molecules, int) or isinstance(
        total_molecules, bool
    ):
        raise TypeError("total_molecules must be an integer.")

    if total_molecules <= 0:
        raise ValueError("total_molecules must be greater than zero.")

    dmso_mass = dmso_mass_fraction
    water_mass = 1.0 - dmso_mass_fraction

    dmso_moles = dmso_mass / MOLAR_MASS["dmso"]
    water_moles = water_mass / MOLAR_MASS["water"]

    total_moles = dmso_moles + water_moles

    target_mole_fraction = (
        dmso_moles / total_moles if total_moles else 0.0
    )

    return calculate_from_mole_fraction(
        target_mole_fraction,
        total_molecules,
    )


def _validate_fraction(value: float) -> None:
    """Validate a fraction expressed between zero and one."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError("Fraction must be a number between 0 and 1.")

    if not 0.0 <= value <= 1.0:
        raise ValueError("Fraction must be between 0 and 1.")


def _build_result(
    water_count: int,
    dmso_count: int,
    requested_fraction: float,
    fraction_type: str,
) -> MixtureComposition:
    """Calculate achieved fractions from integer molecule counts."""
    total = water_count + dmso_count

    if total <= 0:
        raise ValueError("At least one molecule is required.")

    dmso_mass = dmso_count * MOLAR_MASS["dmso"]
    water_mass = water_count * MOLAR_MASS["water"]
    total_mass = dmso_mass + water_mass

    mole_fraction = dmso_count / total
    mass_fraction = dmso_mass / total_mass if total_mass else 0.0

    return MixtureComposition(
        water_molecules=water_count,
        dmso_molecules=dmso_count,
        requested_fraction=requested_fraction,
        fraction_type=fraction_type,
        achieved_mole_fraction_dmso=mole_fraction,
        achieved_mass_fraction_dmso=mass_fraction,
    )


def print_composition(result: MixtureComposition) -> None:
    """Print a readable composition summary."""
    print("\nWater-DMSO composition")
    print("-" * 36)
    print(f"Water molecules: {result.water_molecules}")
    print(f"DMSO molecules:  {result.dmso_molecules}")
    print(
        "Total molecules: "
        f"{result.water_molecules + result.dmso_molecules}"
    )
    print(f"Input mode: {result.fraction_type}")
    print(f"Requested fraction: {result.requested_fraction:.6f}")
    print(
        "Achieved DMSO mole fraction: "
        f"{result.achieved_mole_fraction_dmso:.6f}"
    )
    print(
        "Achieved DMSO mass fraction: "
        f"{result.achieved_mass_fraction_dmso:.6f}"
    )


if __name__ == "__main__":
    # Example: 20 mol% DMSO in a mixture of 10,000 molecules.
    result = calculate_from_mole_fraction(
        dmso_mole_fraction=0.20,
        total_molecules=10_000,
    )
    print_composition(result)
