"""Interactive terminal interface for water-DMSO composition calculations."""

from flexsolvmd.solvents.composition import (
    calculate_from_mass_fraction,
    calculate_from_mole_fraction,
    print_composition,
)


def ask_fraction(prompt: str) -> float:
    """Read a fraction between 0 and 1."""
    while True:
        raw_value = input(prompt).strip()

        try:
            value = float(raw_value)
        except ValueError:
            print("Please enter a valid number, such as 0.20.")
            continue

        if not 0.0 <= value <= 1.0:
            print("The fraction must be between 0 and 1.")
            continue

        return value


def ask_total_molecules() -> int:
    """Read a positive integer molecule count."""
    while True:
        raw_value = input("Total solvent molecules: ").strip()

        try:
            total = int(raw_value)
        except ValueError:
            print("Please enter a positive whole number, such as 10000.")
            continue

        if total <= 0:
            print("The total must be greater than zero.")
            continue

        return total


def main() -> None:
    """Run the interactive water-DMSO composition calculator."""
    print("\nFlexSolvMD — Water-DMSO Composition Calculator")
    print("=" * 48)
    print("Choose how to specify the DMSO fraction:")
    print("[1] Mole fraction")
    print("[2] Mass fraction")

    while True:
        choice = input("Your choice [1/2]: ").strip()
        if choice in {"1", "2"}:
            break
        print("Please enter 1 or 2.")

    if choice == "1":
        fraction = ask_fraction("Target DMSO mole fraction (0-1): ")
    else:
        fraction = ask_fraction("Target DMSO mass fraction (0-1): ")

    total = ask_total_molecules()

    try:
        if choice == "1":
            result = calculate_from_mole_fraction(
                dmso_mole_fraction=fraction,
                total_molecules=total,
            )
        else:
            result = calculate_from_mass_fraction(
                dmso_mass_fraction=fraction,
                total_molecules=total,
            )
    except ValueError as exc:
        print(f"\nInput error: {exc}")
        return

    print()
    print_composition(result)
    print("\nNote: This calculates molecule counts only.")
    print("It does not generate coordinates or validate a force field.")


if __name__ == "__main__":
    main()
