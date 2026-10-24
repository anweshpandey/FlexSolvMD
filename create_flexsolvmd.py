from pathlib import Path

root = Path(__file__).resolve().parent

files = {
    "environment.yml": """
name: flexsolvmd
channels:
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - pyyaml
  - pytest
""".lstrip(),

    "pyproject.toml": """
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "flexsolvmd"
version = "0.1.0"
description = "Mixed-solvent molecular dynamics preparation CLI"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0"]

[project.scripts]
flexsolvmd = "flexsolvmd.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
""".lstrip(),

    "config/gromacs.yml": """
installations:
  "2024.5":
    conda_env: gmx24.5
    executable: /home/apandey/miniforge3/envs/gmx24.5/bin.AVX2_256/gmx
  "2025.2":
    conda_env: gmx25
    executable: /home/apandey/miniforge3/envs/gmx25/bin.AVX2_256/gmx
  "5.1.1":
    conda_env: null
    executable: /usr/local/gromacs/bin/gmx
""".lstrip(),

    "src/flexsolvmd/__init__.py": '''
"""FlexSolvMD: mixed-solvent molecular dynamics preparation."""

__version__ = "0.1.0"
'''.lstrip(),

    "src/flexsolvmd/gromacs.py": '''
"""GROMACS installation discovery and version verification."""

from dataclasses import dataclass
import os
import re
import subprocess
from typing import Optional


@dataclass(frozen=True)
class GromacsInstallation:
    version: str
    executable: str
    conda_env: Optional[str] = None


def detect_version(installation: GromacsInstallation) -> str:
    """Run GROMACS and read its reported version."""
    env = os.environ.copy()

    if installation.conda_env:
        prefix = (
            f"/home/apandey/miniforge3/envs/"
            f"{installation.conda_env}"
        )
        env["CONDA_PREFIX"] = prefix
        env["PATH"] = (
            f"{prefix}/bin:"
            f"{prefix}/bin.AVX2_256:"
            f"{env.get('PATH', '')}"
        )

        lib = f"{prefix}/lib"
        env["LD_LIBRARY_PATH"] = (
            lib + ":" + env.get("LD_LIBRARY_PATH", "")
        )

    result = subprocess.run(
        [installation.executable, "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        check=False,
    )

    output = result.stdout + "\\n" + result.stderr

    if result.returncode != 0:
        raise RuntimeError(
            f"GROMACS verification failed for "
            f"{installation.executable}.\\n"
            f"{result.stderr.strip()}"
        )

    match = re.search(
        r"GROMACS version:\\s*([^\\s]+)",
        output,
    )

    if not match:
        match = re.search(
            r"GROMACS\\s*-\\s*gmx,\\s*([^\\s]+)",
            output,
        )

    if not match:
        raise RuntimeError(
            "Could not parse the GROMACS version."
        )

    return match.group(1).removesuffix("-conda_forge")


def verify_installation(
    installation: GromacsInstallation,
) -> str:
    actual = detect_version(installation)

    if actual != installation.version:
        raise RuntimeError(
            f"Expected GROMACS {installation.version}, "
            f"but executable reports {actual}."
        )

    return actual
'''.lstrip(),

    "src/flexsolvmd/cli.py": '''
"""Interactive FlexSolvMD command-line interface."""

import subprocess
from pathlib import Path

import yaml

from flexsolvmd import __version__
from flexsolvmd.gromacs import (
    GromacsInstallation,
    verify_installation,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "gromacs.yml"


def load_installations():
    with CONFIG.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    return [
        GromacsInstallation(
            version=version,
            executable=settings["executable"],
            conda_env=settings.get("conda_env"),
        )
        for version, settings
        in config["installations"].items()
    ]


def main():
    print()
    print("=" * 54)
    print("                  FlexSolvMD")
    print("      Mixed-Solvent Molecular Dynamics Prep")
    print(f"                  Version {__version__}")
    print("=" * 54)

    installations = load_installations()

    print("\\nSelect your GROMACS installation:\\n")

    for index, installation in enumerate(
        installations, start=1
    ):
        label = (
            f"Conda environment: {installation.conda_env}"
            if installation.conda_env
            else "System installation"
        )

        print(f"  [{index}] GROMACS {installation.version}")
        print(f"      {label}")
        print(f"      {installation.executable}\\n")

    print("  [Q] Quit\\n")

    choice = input("Your choice: ").strip().lower()

    if choice in {"q", "quit", "exit"}:
        print("FlexSolvMD closed.")
        return

    if (
        not choice.isdigit()
        or not 1 <= int(choice) <= len(installations)
    ):
        print("Invalid selection. Please try again.")
        return

    selected = installations[int(choice) - 1]

    print(f"\\nChecking GROMACS {selected.version}...")

    try:
        actual = verify_installation(selected)
    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print("\\nERROR: GROMACS verification failed.")
        print(exc)
        print("No molecular system was created.")
        return

    print(f"Verified GROMACS version: {actual}")
    print(f"Executable: {selected.executable}")
    print("\\nInstallation check passed.")
    print("\\nThe preparation workflow is not implemented yet.")
    print("Next: protein/ligand validation and water-DMSO")
    print("composition calculations.")


if __name__ == "__main__":
    main()
'''.lstrip(),

    "README.md": """
# FlexSolvMD

A terminal-based Python tool for preparing mixed-solvent
molecular dynamics systems and performing energy minimization.

The workflow ends after minimization; it does not automatically
start NVT, NPT, or production molecular dynamics.

## Initial capabilities

- Interactive GROMACS version selection
- Executable version verification
- Separate Python environment
- Central GROMACS configuration

## Planned capabilities

- Protein and ligand input validation
- Force-field compatibility checks
- Water-DMSO composition calculations
- Solvent-box construction and topology integration
- Energy minimization and output validation
- JSON and Markdown reports

Successful minimization alone does not establish equilibrium
or scientific validity of the molecular model.
""".lstrip(),

    "tests/test_gromacs.py": '''
from flexsolvmd.gromacs import GromacsInstallation


def test_installations_have_expected_paths():
    installation = GromacsInstallation(
        "2024.5",
        "/home/apandey/miniforge3/envs/"
        "gmx24.5/bin.AVX2_256/gmx",
        "gmx24.5",
    )

    assert installation.conda_env == "gmx24.5"
'''.lstrip(),
}


for relative_path, content in files.items():
    destination = root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"Created: {destination}")


for folder in (
    "src/flexsolvmd/solvents",
    "src/flexsolvmd/forcefields",
    "src/flexsolvmd/preparation",
    "src/flexsolvmd/validation",
    "src/flexsolvmd/reporting",
):
    path = root / folder
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").touch(exist_ok=True)


print("\\nFlexSolvMD starter source code created.")
