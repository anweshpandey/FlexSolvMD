"""Ligand parameterization using ACPYPE."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LigandParameterizationResult:
    """Paths and metadata for a completed ACPYPE conversion."""

    input_file: Path
    output_dir: Path
    coordinate_file: Path
    topology_file: Path
    include_file: Path
    atom_type: str
    charge_method: str
    net_charge: int


class LigandParameterizationError(RuntimeError):
    """Raised when ligand parameterization fails or produces invalid output."""


def parameterize_ligand(
    input_file: str | Path,
    output_dir: str | Path,
    *,
    basename: str | None = None,
    net_charge: int = 0,
    atom_type: str = "gaff2",
    charge_method: str = "bcc",
    executable: str = "acpype",
    timeout_seconds: int = 600,
    overwrite: bool = False,
) -> LigandParameterizationResult:
    """Convert a prepared ligand structure to GROMACS files using ACPYPE.

    The input must already contain a chemically valid ligand structure.
    This function does not generate coordinates or validate the scientific
    suitability of the selected ligand force-field parameters.
    """

    source = Path(input_file).expanduser().resolve()
    destination = Path(output_dir).expanduser().resolve()

    if not source.is_file():
        raise LigandParameterizationError(
            f"Ligand input file does not exist: {source}"
        )

    if not isinstance(net_charge, int) or isinstance(net_charge, bool):
        raise LigandParameterizationError(
            "net_charge must be an integer."
        )

    if atom_type not in {"gaff", "gaff2"}:
        raise LigandParameterizationError(
            "atom_type must be 'gaff' or 'gaff2'."
        )

    if charge_method not in {"bcc", "gas", "mul", "user", "rc"}:
        raise LigandParameterizationError(
            "Unsupported charge_method. Choose bcc, gas, mul, user, or rc."
        )

    if timeout_seconds <= 0:
        raise LigandParameterizationError(
            "timeout_seconds must be greater than zero."
        )

    if basename is None:
        basename = source.stem

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", basename):
        raise LigandParameterizationError(
            "basename may contain only letters, digits, dots, underscores, "
            "and hyphens, and must begin with a letter or digit."
        )

    if basename in {".", ".."}:
        raise LigandParameterizationError("Invalid basename.")

    resolved_executable = shutil.which(executable)
    if resolved_executable is None:
        candidate = Path(executable).expanduser()
        if candidate.is_file():
            resolved_executable = str(candidate.resolve())
        else:
            raise LigandParameterizationError(
                f"ACPYPE executable not found: {executable}"
            )

    result_dir = destination / f"{basename}.acpype"

    if result_dir.exists() and not overwrite:
        raise LigandParameterizationError(
            f"Output directory already exists: {result_dir}. "
            "Choose another basename or explicitly set overwrite=True."
        )

    destination.mkdir(parents=True, exist_ok=True)

    command = [
        resolved_executable,
        "-i", str(source),
        "-b", basename,
        "-c", charge_method,
        "-n", str(net_charge),
        "-a", atom_type,
        "-o", "gmx",
        "-s", "180",
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=destination,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise LigandParameterizationError(
            f"ACPYPE exceeded the {timeout_seconds}-second timeout."
        ) from exc
    except OSError as exc:
        raise LigandParameterizationError(
            f"Could not execute ACPYPE: {exc}"
        ) from exc

    log_path = destination / f"{basename}_acpype.log"
    log_path.write_text(
        "COMMAND: " + " ".join(command) + "\n\n"
        + "=== STDOUT ===\n" + (completed.stdout or "")
        + "\n=== STDERR ===\n" + (completed.stderr or ""),
        encoding="utf-8",
    )

    if completed.returncode != 0:
        raise LigandParameterizationError(
            f"ACPYPE failed with exit code {completed.returncode}. "
            f"See log: {log_path}"
        )

    coordinate_file = result_dir / f"{basename}_GMX.gro"
    topology_file = result_dir / f"{basename}_GMX.top"
    include_file = result_dir / f"{basename}_GMX.itp"

    expected_files = (
        coordinate_file,
        topology_file,
        include_file,
    )

    missing = [
        str(path) for path in expected_files
        if not path.is_file() or path.stat().st_size == 0
    ]

    if missing:
        raise LigandParameterizationError(
            "ACPYPE returned success but required output files are missing "
            "or empty: " + ", ".join(missing)
            + f". See log: {log_path}"
        )

    return LigandParameterizationResult(
        input_file=source,
        output_dir=result_dir,
        coordinate_file=coordinate_file,
        topology_file=topology_file,
        include_file=include_file,
        atom_type=atom_type,
        charge_method=charge_method,
        net_charge=net_charge,
    )
