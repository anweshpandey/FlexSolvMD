import pytest

from flexsolvmd.validation.protein import (
    ProteinValidationError,
    inspect_protein_pdb,
)


def atom_line(
    serial, atom, residue="ALA", chain="A", resseq=1,
    record="ATOM", altloc="",
):
    return (
        f"{record:<6}{serial:5d} {atom:4s}{altloc:1s}"
        f"{residue:>3s} {chain:1s}{resseq:4d}    "
        f"{1.0:8.3f}{2.0:8.3f}{3.0:8.3f}"
        f"{1.0:6.2f}{20.0:6.2f}          {atom[0]:>2s}"
    )


def test_inspects_simple_protein_pdb(tmp_path):
    path = tmp_path / "protein.pdb"
    path.write_text(
        atom_line(1, "N") + "\n"
        + atom_line(2, "CA") + "\n"
        + "TER\nEND\n"
    )

    result = inspect_protein_pdb(path)

    assert result.atom_records == 2
    assert result.protein_atom_records == 2
    assert result.residues == 1
    assert result.chains == ("A",)
    assert result.has_ter_records
    assert result.has_end_record


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(ProteinValidationError, match="does not exist"):
        inspect_protein_pdb(tmp_path / "missing.pdb")


def test_file_without_atoms_is_rejected(tmp_path):
    path = tmp_path / "empty_structure.pdb"
    path.write_text("HEADER    EMPTY STRUCTURE\nEND\n")

    with pytest.raises(ProteinValidationError, match="No ATOM"):
        inspect_protein_pdb(path)


def test_alternate_locations_are_reported(tmp_path):
    path = tmp_path / "alternate.pdb"
    path.write_text(
        atom_line(1, "CA", altloc="A") + "\n"
        + atom_line(2, "CA", altloc="B") + "\n"
        + "TER\nEND\n"
    )

    result = inspect_protein_pdb(path)

    assert result.alternate_locations == ("A", "B")
    assert any("Alternate-location" in warning for warning in result.warnings)


def test_non_protein_residues_are_reported(tmp_path):
    path = tmp_path / "with_ligand.pdb"
    path.write_text(
        atom_line(1, "CA") + "\n"
        + atom_line(2, "C1", residue="LIG", record="HETATM") + "\n"
        + "TER\nEND\n"
    )

    result = inspect_protein_pdb(path)

    assert "LIG" in result.non_protein_residues
    assert any("Non-protein residues" in w for w in result.warnings)


def test_multiple_models_are_reported(tmp_path):
    path = tmp_path / "models.pdb"
    path.write_text(
        "MODEL        1\n"
        + atom_line(1, "CA") + "\nENDMDL\n"
        + "MODEL        2\n"
        + atom_line(1, "CA") + "\nENDMDL\n"
        + "END\n"
    )

    result = inspect_protein_pdb(path)

    assert result.model_count == 2
    assert any("MODEL records" in warning for warning in result.warnings)
