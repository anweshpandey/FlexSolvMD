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

    output = result.stdout + "\n" + result.stderr

    if result.returncode != 0:
        raise RuntimeError(
            f"GROMACS verification failed for "
            f"{installation.executable}.\n"
            f"{result.stderr.strip()}"
        )

    match = re.search(
        r"GROMACS version:\s*([^\s]+)",
        output,
    )

    if not match:
        match = re.search(
            r"GROMACS\s*-\s*gmx,\s*([^\s]+)",
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
