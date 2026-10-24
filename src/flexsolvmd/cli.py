"""Interactive FlexSolvMD command-line interface."""

import subprocess
from pathlib import Path

import yaml

from flexsolvmd import __version__
from flexsolvmd.gromacs import (
    GromacsInstallation,
    verify_installation,
)
from flexsolvmd.solvents.interactive import (
    main as composition_main,
)
from flexsolvmd.toolchain import (
    inspect_default_toolchain,
    inspect_gromacs_installations,
    print_tool_status,
)
from flexsolvmd.validation.protein import (
    ProteinValidationError,
    inspect_protein_pdb,
    print_protein_inspection,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "gromacs.yml"


def load_installations():
    """Load configured GROMACS installations."""
    with CONFIG.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    return [
        GromacsInstallation(
            version=version,
            executable=settings["executable"],
            conda_env=settings.get("conda_env"),
        )
        for version, settings in config["installations"].items()
    ]


def check_gromacs():
    """Let the user select and verify a GROMACS installation."""
    installations = load_installations()

    print("\nSelect your GROMACS installation:\n")

    for index, installation in enumerate(installations, start=1):
        label = (
            f"Conda environment: {installation.conda_env}"
            if installation.conda_env
            else "System installation"
        )

        print(f"  [{index}] GROMACS {installation.version}")
        print(f"      {label}")
        print(f"      {installation.executable}\n")

    print("  [B] Back to main menu")
    choice = input("\nYour choice: ").strip().lower()

    if choice in {"b", "back"}:
        return

    if (
        not choice.isdigit()
        or not 1 <= int(choice) <= len(installations)
    ):
        print("Invalid selection.")
        return

    selected = installations[int(choice) - 1]

    print(f"\nChecking GROMACS {selected.version}...")

    try:
        actual = verify_installation(selected)
    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print("\nERROR: GROMACS verification failed.")
        print(exc)
        print("No molecular system was created.")
        return

    print(f"\nVerified GROMACS version: {actual}")
    print(f"Executable: {selected.executable}")
    print("Installation check passed.")


def inspect_protein():
    """Interactively inspect a protein PDB without modifying it."""
    print("\nInspect protein PDB")
    print("-" * 30)
    filename = input("Path to protein PDB (or B to go back): ").strip()

    if filename.lower() in {"b", "back"}:
        return

    if not filename:
        print("No file path provided.")
        return

    try:
        result = inspect_protein_pdb(filename)
    except (ProteinValidationError, OSError) as exc:
        print(f"Protein inspection failed: {exc}")
        return

    print_protein_inspection(result)


def check_toolchain():
    """Check external-tool availability without launching the tools."""
    print("\nConfigured GROMACS installations")
    print("-" * 36)

    for status in inspect_gromacs_installations().values():
        print_tool_status(status)

    print("\nOther external tools")
    print("-" * 36)

    for status in inspect_default_toolchain():
        print_tool_status(status)

    print(
        "\nThis check only verifies executable availability. "
        "It does not prove that the tools work together."
    )


def show_banner():
    """Display the application banner."""
    print()
    print("=" * 54)
    print("                  FlexSolvMD")
    print("      Mixed-Solvent Molecular Dynamics Prep")
    print(f"                  Version {__version__}")
    print("=" * 54)


def main():
    """Run the main interactive menu."""
    show_banner()

    while True:
        print("\nMain menu")
        print("-" * 30)
        print("[1] Check GROMACS installation")
        print("[2] Calculate water-DMSO composition")
        print("[3] Check external-tool availability")
        print("[4] Inspect protein PDB")
        print("[Q] Quit")

        choice = input("\nYour choice: ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            print("FlexSolvMD closed.")
            break

        elif choice == "1":
            check_gromacs()

        elif choice == "2":
            composition_main()

        elif choice == "3":
            check_toolchain()

        elif choice == "4":
            inspect_protein()

        else:
            print("Invalid selection. Please enter 1, 2, 3, 4, or Q.")


if __name__ == "__main__":
    main()
