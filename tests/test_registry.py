import pytest

from flexsolvmd.solvents.registry import (
    DMSO_MODELS,
    PROTEIN_FORCE_FIELDS,
    WATER_MODELS,
    get_model,
    list_models,
    validate_registry_selection,
)


def test_water_models_are_registered():
    assert set(WATER_MODELS) == {"tip3p", "tip4p", "spce"}


def test_amber99sb_ildn_is_registered():
    model = get_model("protein_forcefield", "amber99sb-ildn")

    assert model.name == "AMBER99SB-ILDN"
    assert model.category == "protein_forcefield"


def test_fox_kollman_dmso_candidate_is_registered():
    model = get_model("dmso", "fox-kollman-1998")

    assert model.category == "dmso"
    assert model.provenance is not None
    assert "10.1021/jp9717655" in model.provenance


def test_dmso_candidate_is_not_marked_validated():
    model = get_model("dmso", "fox-kollman-1998")

    assert model.status == "candidate_requires_parameter_audit"
    assert model.status != "validated"


def test_water_model_lookup_is_case_insensitive():
    model = get_model("water", "TIP3P")

    assert model.identifier == "tip3p"


def test_unknown_water_model_is_rejected():
    with pytest.raises(ValueError, match="Unknown water model"):
        get_model("water", "unknown-water-model")


def test_unknown_category_is_rejected():
    with pytest.raises(ValueError, match="Unknown model category"):
        list_models("unknown-category")


def test_unregistered_dmso_model_is_rejected():
    with pytest.raises(ValueError, match="Unknown dmso model"):
        get_model("dmso", "placeholder")


def test_catalogue_models_are_not_marked_validated():
    models = list(WATER_MODELS.values()) + list(
        PROTEIN_FORCE_FIELDS.values()
    )

    assert models
    assert all(model.status == "catalog_only" for model in models)


def test_unvalidated_dmso_selection_is_rejected():
    with pytest.raises(ValueError, match="not marked as validated"):
        validate_registry_selection(
            water_model="tip3p",
            protein_forcefield="amber99sb-ildn",
            dmso_model="fox-kollman-1998",
        )
