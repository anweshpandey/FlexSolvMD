import pytest

from flexsolvmd.solvents.composition import (
    calculate_from_mass_fraction,
    calculate_from_mole_fraction,
)


def test_mole_fraction_calculation():
    result = calculate_from_mole_fraction(
        dmso_mole_fraction=0.20,
        total_molecules=10_000,
    )

    assert result.water_molecules == 8_000
    assert result.dmso_molecules == 2_000
    assert result.water_molecules + result.dmso_molecules == 10_000
    assert result.achieved_mole_fraction_dmso == pytest.approx(0.20)


def test_pure_water():
    result = calculate_from_mole_fraction(
        dmso_mole_fraction=0.0,
        total_molecules=1_000,
    )

    assert result.water_molecules == 1_000
    assert result.dmso_molecules == 0


def test_pure_dmso():
    result = calculate_from_mole_fraction(
        dmso_mole_fraction=1.0,
        total_molecules=1_000,
    )

    assert result.water_molecules == 0
    assert result.dmso_molecules == 1_000


def test_mass_fraction_calculation():
    result = calculate_from_mass_fraction(
        dmso_mass_fraction=0.50,
        total_molecules=10_000,
    )

    assert result.water_molecules + result.dmso_molecules == 10_000
    assert result.achieved_mass_fraction_dmso == pytest.approx(
        0.50, abs=0.001
    )


@pytest.mark.parametrize("fraction", [-0.1, 1.1])
def test_invalid_mole_fraction(fraction):
    with pytest.raises(ValueError):
        calculate_from_mole_fraction(
            dmso_mole_fraction=fraction,
            total_molecules=1_000,
        )


@pytest.mark.parametrize("total", [0, -1, 1.5])
def test_invalid_total_molecule_count(total):
    with pytest.raises(ValueError):
        calculate_from_mole_fraction(
            dmso_mole_fraction=0.20,
            total_molecules=total,
        )
