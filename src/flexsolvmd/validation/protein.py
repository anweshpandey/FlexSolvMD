"""Read-only structural inspection for protein PDB files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProteinInspection:
    """Summary of a PDB inspection; warnings require human review."""

    path: Path
    atom_records: int
    protein_atom_records: int
    residues: int
    chains: tuple[str, ...]
    alternate_locations: tuple[str, ...]
    model_count: int
    has_ter_records: bool
    has_end_record: bool
    non_protein_residues: tuple[str, ...]
    warnings: tuple[str, ...]


# Common amino-acid residue names, including common protonation variants.
AMINO_ACIDS = {
    "ALA", "ARG", "ASN", "ASP", "ASH", "CYS", "CYM", "CYX",
    "GLN", "GLU", "GLH", "GLY", "HIS", "HID", "HIE", "HIP",
    "ILE", "LEU", "LYS", "LYN", "MET", "PHE", "PRO", "SER",
    "THR", "TRP", "TYR", "VAL", "ACE", "NME",
}

WATER_RESIDUES = {"HOH", "WAT", "SOL", "TIP3", "TIP4", "SPC"}


class ProteinValidationError(ValueError):
    """Raised when a PDB cannot be inspected safely."""


def inspect_protein_pdb(input_file: str | Path) -> ProteinInspection:
    """Inspect a PDB without changing it or claiming it is simulation-ready."""

    path = Path(input_file).expanduser().resolve()

    if not path.is_file():
        raise ProteinValidationError(f"PDB file does not exist: {path}")

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise ProteinValidationError(f"Cannot read PDB file: {exc}") from exc

    if not lines:
        raise ProteinValidationError("PDB file is empty.")

    atom_records = 0
    protein_atom_records = 0
    residues: set[tuple[str, str, str, str]] = set()
    chains: set[str] = set()
    alternate_locations: set[str] = set()
    non_protein_residues: set[str] = set()
    models: set[str] = set()
    warnings: list[str] = []

    has_ter = False
    has_end = False
    has_model_records = False
    has_atom_serials: set[str] = set()
    duplicate_serials: set[str] = set()
    malformed_atom_lines = 0

    for line_number, line in enumerate(lines, start=1):
        record = line[:6].strip().upper()

        if record == "MODEL":
            has_model_records = True
            models.add(line[10:14].strip() or str(line_number))
            continue

        if record == "ENDMDL":
            continue

        if record == "TER":
            has_ter = True
            continue

        if record == "END":
            has_end = True
            continue

        if record not in {"ATOM", "HETATM"}:
            continue

        atom_records += 1

        if len(line) < 54:
            malformed_atom_lines += 1
            continue

        serial = line[6:11].strip()
        if serial:
            if serial in has_atom_serials:
                duplicate_serials.add(serial)
            has_atom_serials.add(serial)

        atom_name = line[12:16].strip()
        altloc = line[16:17].strip()
        resname = line[17:20].strip().upper()
        chain = line[21:22].strip() or "_"
        resseq = line[22:26].strip()
        icode = line[26:27].strip()

        if not atom_name or not resname or not resseq:
            malformed_atom_lines += 1
            continue

        if altloc:
            alternate_locations.add(altloc)

        residues.add((chain, resseq, icode, resname))
        chains.add(chain)

        if resname in AMINO_ACIDS and record == "ATOM":
            protein_atom_records += 1
        elif resname not in WATER_RESIDUES:
            non_protein_residues.add(resname)

    if atom_records == 0:
        raise ProteinValidationError(
            "No ATOM or HETATM records were found in the input."
        )

    if protein_atom_records == 0:
        raise ProteinValidationError(
            "No recognized standard amino-acid ATOM records were found. "
            "This may not be a protein PDB, or it may use unsupported "
            "residue naming."
        )

    if malformed_atom_lines:
        warnings.append(
            f"{malformed_atom_lines} atom record(s) were too short or "
            "had missing essential fields."
        )

    if duplicate_serials:
        warnings.append(
            "Duplicate atom serial number(s) found: "
            + ", ".join(sorted(duplicate_serials))
            + ". Check model boundaries and serial numbering."
        )

    if alternate_locations:
        warnings.append(
            "Alternate-location labels found: "
            + ", ".join(sorted(alternate_locations))
            + ". Select or resolve conformations before preparation."
        )

    model_count = len(models) if has_model_records else 1
    if model_count > 1:
        warnings.append(
            f"The file contains {model_count} MODEL records. "
            "Choose a model explicitly before preparation."
        )

    if not has_ter:
        warnings.append(
            "No TER record was found. Chain boundaries should be reviewed; "
            "TER is not required in every valid PDB."
        )

    if not has_end:
        warnings.append(
            "No END record was found. The file may still be readable, "
            "but check that it is complete."
        )

    if non_protein_residues:
        warnings.append(
            "Non-protein residues detected: "
            + ", ".join(sorted(non_protein_residues))
            + ". Determine which are ligands, cofactors, ions, or other "
            "components before deciding whether to retain them."
        )

    if len(chains) > 1:
        warnings.append(
            f"Multiple chain identifiers found ({len(chains)}). "
            "Review chain selection and inter-chain connectivity."
        )

    return ProteinInspection(
        path=path,
        atom_records=atom_records,
        protein_atom_records=protein_atom_records,
        residues=len(residues),
        chains=tuple(sorted(chains)),
        alternate_locations=tuple(sorted(alternate_locations)),
        model_count=model_count,
        has_ter_records=has_ter,
        has_end_record=has_end,
        non_protein_residues=tuple(sorted(non_protein_residues)),
        warnings=tuple(warnings),
    )


def print_protein_inspection(result: ProteinInspection) -> None:
    """Print an inspection summary for a terminal user."""

    print("\nProtein PDB inspection")
    print("-" * 32)
    print(f"File:                 {result.path}")
    print(f"ATOM/HETATM records:  {result.atom_records}")
    print(f"Protein ATOM records: {result.protein_atom_records}")
    print(f"Residues:             {result.residues}")
    print(f"Chains:               {', '.join(result.chains)}")
    print(f"Structural models:    {result.model_count}")
    print(f"TER record present:   {result.has_ter_records}")
    print(f"END record present:   {result.has_end_record}")

    if result.non_protein_residues:
        print(
            "Other residues:       "
            + ", ".join(result.non_protein_residues)
        )

    if result.warnings:
        print("\nWarnings for review:")
        for warning in result.warnings:
            print(f"  - {warning}")
    else:
        print("\nNo basic structural warnings detected.")

    print(
        "\nThis is a preliminary file inspection, not proof that the "
        "structure is complete or ready for molecular dynamics."
    )
