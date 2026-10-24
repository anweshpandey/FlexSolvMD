"""Registry of solvent and force-field models.

Catalogue entries are descriptive metadata, not proof of compatibility.
A combination must be validated before it is used to build a simulation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDefinition:
    """Describe a molecular model and its validation status."""

    identifier: str
    name: str
    category: str
    status: str
    description: str
    provenance: str | None = None


WATER_MODELS = {
    "tip3p": ModelDefinition(
        identifier="tip3p",
        name="TIP3P",
        category="water",
        status="catalog_only",
        description="Three-site rigid water model.",
    ),
    "tip4p": ModelDefinition(
        identifier="tip4p",
        name="TIP4P",
        category="water",
        status="catalog_only",
        description="Four-site water model with a virtual charge site.",
    ),
    "spce": ModelDefinition(
        identifier="spce",
        name="SPC/E",
        category="water",
        status="catalog_only",
        description="Three-site water model with an electronic "
        "continuum correction.",
    ),
}


PROTEIN_FORCE_FIELDS = {
    "amber99sb-ildn": ModelDefinition(
        identifier="amber99sb-ildn",
        name="AMBER99SB-ILDN",
        category="protein_forcefield",
        status="catalog_only",
        description="Amber-family protein force field.",
    ),
}


DMSO_MODELS = {
    "fox-kollman-1998": ModelDefinition(
        identifier="fox-kollman-1998",
        name="Fox-Kollman 1998 all-atom DMSO",
        category="dmso",
        status="candidate_requires_parameter_audit",
        description=(
            "Literature-supported AMBER-compatible DMSO model. "
            "Parameter files, topology conversion, and the selected "
            "water-model pairing must be audited before use."
        ),
        provenance=(
            "Fox and Kollman, J. Phys. Chem. B 102 (1998), 8070-8079. "
            "DOI: 10.1021/jp9717655"
        ),
    ),
}


def list_models(category: str) -> list[ModelDefinition]:
    """Return models registered for a category."""
    catalogues = {
        "water": WATER_MODELS,
        "protein_forcefield": PROTEIN_FORCE_FIELDS,
        "dmso": DMSO_MODELS,
    }

    if category not in catalogues:
        allowed = ", ".join(sorted(catalogues))
        raise ValueError(
            f"Unknown model category {category!r}. "
            f"Choose from: {allowed}."
        )

    return list(catalogues[category].values())


def get_model(category: str, identifier: str) -> ModelDefinition:
    """Retrieve one model using its category and identifier."""
    catalogues = {
        "water": WATER_MODELS,
        "protein_forcefield": PROTEIN_FORCE_FIELDS,
        "dmso": DMSO_MODELS,
    }

    if category not in catalogues:
        raise ValueError(f"Unknown model category: {category!r}.")

    try:
        return catalogues[category][identifier.lower()]
    except KeyError:
        available = ", ".join(sorted(catalogues[category])) or "none registered"
        raise ValueError(
            f"Unknown {category} model {identifier!r}. "
            f"Registered identifiers: {available}."
        ) from None


def validate_registry_selection(
    water_model: str,
    protein_forcefield: str,
    dmso_model: str,
) -> list[str]:
    """Check registry references and report unresolved validation.

    This function deliberately does not declare molecular models
    compatible merely because their names appear in the catalogue.
    """
    selected = [
        get_model("water", water_model),
        get_model("protein_forcefield", protein_forcefield),
        get_model("dmso", dmso_model),
    ]

    unresolved = [
        model.name
        for model in selected
        if model.status != "validated"
    ]

    if unresolved:
        names = ", ".join(unresolved)
        raise ValueError(
            "Cannot approve this model selection: the following entries "
            f"are not marked as validated: {names}. "
            "Confirm parameter provenance and compatibility before use."
        )

    return [model.identifier for model in selected]
