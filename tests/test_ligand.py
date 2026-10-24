import subprocess

import pytest

from flexsolvmd.preparation.ligand import (
    LigandParameterizationError,
    parameterize_ligand,
)


def fake_acpype(command, **kwargs):
    """Simulate ACPYPE generating its three required GROMACS files."""
    workdir = kwargs["cwd"]
    basename = command[command.index("-b") + 1]
    result_dir = workdir / f"{basename}.acpype"
    result_dir.mkdir()

    (result_dir / f"{basename}_GMX.gro").write_text(
        "Test ligand\n1\n    1LIG     C1    1   0.000   0.000   0.000\n"
        "   2.00000   2.00000   2.00000\n"
    )
    (result_dir / f"{basename}_GMX.top").write_text(
        '#include "' + basename + '_GMX.itp"\n'
    )
    (result_dir / f"{basename}_GMX.itp").write_text(
        "[ moleculetype ]\nLIG 3\n"
    )

    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout="ACPYPE test completed",
        stderr="",
    )


def test_parameterize_ligand_returns_expected_files(tmp_path, monkeypatch):
    source = tmp_path / "ligand.mol2"
    source.write_text("@<TRIPOS>MOLECULE\nLIG\n")

    monkeypatch.setattr(
        "flexsolvmd.preparation.ligand.shutil.which",
        lambda _: "/mock/acpype",
    )
    monkeypatch.setattr(
        "flexsolvmd.preparation.ligand.subprocess.run",
        fake_acpype,
    )

    result = parameterize_ligand(
        source,
        tmp_path / "output",
        net_charge=0,
        atom_type="gaff2",
    )

    assert result.coordinate_file.is_file()
    assert result.topology_file.is_file()
    assert result.include_file.is_file()
    assert result.atom_type == "gaff2"
    assert result.net_charge == 0
    assert (tmp_path / "output" / "ligand_acpype.log").is_file()


def test_missing_input_is_rejected(tmp_path):
    with pytest.raises(LigandParameterizationError, match="does not exist"):
        parameterize_ligand(
            tmp_path / "missing.mol2",
            tmp_path / "output",
        )


def test_invalid_atom_type_is_rejected(tmp_path):
    source = tmp_path / "ligand.mol2"
    source.write_text("placeholder")

    with pytest.raises(LigandParameterizationError, match="atom_type"):
        parameterize_ligand(
            source,
            tmp_path / "output",
            atom_type="unsupported",
        )


def test_existing_output_is_not_overwritten_by_default(tmp_path, monkeypatch):
    source = tmp_path / "ligand.mol2"
    source.write_text("placeholder")

    destination = tmp_path / "output"
    existing = destination / "ligand.acpype"
    existing.mkdir(parents=True)

    monkeypatch.setattr(
        "flexsolvmd.preparation.ligand.shutil.which",
        lambda _: "/mock/acpype",
    )

    with pytest.raises(LigandParameterizationError, match="already exists"):
        parameterize_ligand(source, destination)


def test_nonzero_acpype_exit_is_reported(tmp_path, monkeypatch):
    source = tmp_path / "ligand.mol2"
    source.write_text("placeholder")

    monkeypatch.setattr(
        "flexsolvmd.preparation.ligand.shutil.which",
        lambda _: "/mock/acpype",
    )
    monkeypatch.setattr(
        "flexsolvmd.preparation.ligand.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args, returncode=2, stdout="", stderr="parameterization error"
        ),
    )

    with pytest.raises(LigandParameterizationError, match="exit code 2"):
        parameterize_ligand(source, tmp_path / "output")
