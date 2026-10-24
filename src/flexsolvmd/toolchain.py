"""Discovery and safe diagnostics for external FlexSolvMD tools."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


GROMACS_PATHS = {
    "2024.5": (
        "/home/apandey/miniforge3/envs/gmx24.5/"
        "bin.AVX2_256/gmx"
    ),
    "2025.2": (
        "/home/apandey/miniforge3/envs/gmx25/"
        "bin.AVX2_256/gmx"
    ),
    "5.1.1": "/usr/local/gromacs/bin/gmx",
}


@dataclass(frozen=True)
class ToolDefinition:
    """Description of an external executable."""

    name: str
    executable: str
    required: bool = False
    purpose: str = ""


@dataclass(frozen=True)
class ToolStatus:
    """Availability and optional diagnostic information for a tool."""

    name: str
    executable: Optional[str]
    available: bool
    required: bool
    purpose: str
    diagnostic: Optional[str] = None
    error: Optional[str] = None


def default_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Return the initial external-tool catalogue."""

    return (
        ToolDefinition(
            name="GROMACS (PATH)",
            executable="gmx",
            purpose="General GROMACS command discovery",
        ),
        ToolDefinition(
            name="ACPYPE",
            executable="acpype",
            required=True,
            purpose="Convert supported ligand parameters to GROMACS format",
        ),
        ToolDefinition(
            name="AmberTools antechamber",
            executable="antechamber",
            required=True,
            purpose="Ligand atom typing and charge preparation",
        ),
        ToolDefinition(
            name="AmberTools parmchk2",
            executable="parmchk2",
            purpose="Inspect missing or uncertain ligand parameters",
        ),
        ToolDefinition(
            name="AmberTools tleap",
            executable="tleap",
            purpose="Build and inspect AMBER-format topologies",
        ),
        ToolDefinition(
            name="Open Babel",
            executable="obabel",
            purpose="Molecular structure conversion when needed",
        ),
        ToolDefinition(
            name="PACKMOL",
            executable="packmol",
            required=True,
            purpose="Construct initial molecular packing configurations",
        ),
    )


def resolve_executable(
    executable: str,
    extra_paths: tuple[str, ...] = (),
) -> Optional[str]:
    """Resolve an executable from explicit paths or the current PATH."""

    candidate = Path(executable).expanduser()

    if candidate.is_absolute() and candidate.is_file():
        if os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        return None

    for raw_path in extra_paths:
        path = Path(raw_path).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())

    discovered = shutil.which(executable)
    if discovered:
        return str(Path(discovered).resolve())

    return None


def inspect_tool(
    definition: ToolDefinition,
    *,
    extra_paths: tuple[str, ...] = (),
    timeout_seconds: int = 10,
    run_diagnostic: bool = False,
) -> ToolStatus:
    """Check availability and optionally collect safe diagnostic output.

    PACKMOL is deliberately not executed here: it normally reads an input
    file from standard input and can wait indefinitely if invoked incorrectly.
    """

    executable = resolve_executable(
        definition.executable,
        extra_paths=extra_paths,
    )

    if executable is None:
        return ToolStatus(
            name=definition.name,
            executable=None,
            available=False,
            required=definition.required,
            purpose=definition.purpose,
            error="Executable not found or not executable.",
        )

    if (
        definition.name.strip().casefold() == "packmol"
        or Path(definition.executable).name.casefold() == "packmol"
    ):
        return ToolStatus(
            name=definition.name,
            executable=executable,
            available=True,
            required=definition.required,
            purpose=definition.purpose,
            diagnostic=(
                "Executable found. Version probing skipped because PACKMOL "
                "normally reads its input from standard input."
            ),
        )

    if not run_diagnostic:
        return ToolStatus(
            name=definition.name,
            executable=executable,
            available=True,
            required=definition.required,
            purpose=definition.purpose,
            diagnostic=(
                "Executable found. Version/help probe skipped "
                "in safe availability-only mode."
            ),
        )

    arguments = {
        "gmx": ["--version"],
        "acpype": ["--help"],
        "antechamber": ["-h"],
        "parmchk2": ["-h"],
        "tleap": ["-h"],
        "obabel": ["-V"],
    }.get(Path(definition.executable).name, ["--help"])

    try:
        result = subprocess.run(
            [executable, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        output = (result.stdout + "\n" + result.stderr).strip()
        first_lines = "\n".join(output.splitlines()[:5]) or (
            "Command returned no diagnostic text."
        )

        return ToolStatus(
            name=definition.name,
            executable=executable,
            available=True,
            required=definition.required,
            purpose=definition.purpose,
            diagnostic=first_lines,
        )

    except subprocess.TimeoutExpired:
        return ToolStatus(
            name=definition.name,
            executable=executable,
            available=True,
            required=definition.required,
            purpose=definition.purpose,
            error=f"Diagnostic command exceeded {timeout_seconds} seconds.",
        )

    except OSError as exc:
        return ToolStatus(
            name=definition.name,
            executable=executable,
            available=True,
            required=definition.required,
            purpose=definition.purpose,
            error=f"Could not execute diagnostic command: {exc}",
        )


def inspect_gromacs_installations() -> dict[str, ToolStatus]:
    """Inspect the explicitly configured GROMACS executables."""

    results = {}

    for version, executable in GROMACS_PATHS.items():
        definition = ToolDefinition(
            name=f"GROMACS {version}",
            executable=executable,
            required=(version == "2024.5"),
            purpose="Run topology processing and energy minimization",
        )

        results[version] = inspect_tool(definition)

    return results


def inspect_default_toolchain() -> tuple[ToolStatus, ...]:
    """Inspect the initial external-tool catalogue."""

    return tuple(
        inspect_tool(definition)
        for definition in default_tool_definitions()
    )


def print_tool_status(status: ToolStatus) -> None:
    """Print one human-readable diagnostic result."""

    state = "AVAILABLE" if status.available else "MISSING"

    print(f"{status.name}: {state}")

    if status.executable:
        print(f"  Executable: {status.executable}")

    if status.purpose:
        print(f"  Purpose: {status.purpose}")

    if status.diagnostic:
        print("  Diagnostic:")
        for line in status.diagnostic.splitlines():
            print(f"    {line}")

    if status.error:
        print(f"  Note: {status.error}")


if __name__ == "__main__":
    print("FlexSolvMD external-tool audit")
    print("=" * 36)

    print("\nConfigured GROMACS installations")
    for status in inspect_gromacs_installations().values():
        print_tool_status(status)

    print("\nOther external tools")
    for status in inspect_default_toolchain():
        print_tool_status(status)
