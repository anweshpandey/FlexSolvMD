from flexsolvmd.toolchain import (
    GROMACS_PATHS,
    ToolDefinition,
    inspect_tool,
    resolve_executable,
)


def test_gromacs_registry_contains_expected_versions():
    assert set(GROMACS_PATHS) == {"2024.5", "2025.2", "5.1.1"}


def test_resolve_executable_returns_none_for_missing_tool():
    assert resolve_executable("flexsolvmd-definitely-not-a-real-executable") is None


def test_packmol_is_not_executed_during_inspection(tmp_path):
    packmol = tmp_path / "packmol"
    packmol.write_text("#!/bin/sh\nexit 99\n")
    packmol.chmod(0o755)

    definition = ToolDefinition(
        name="PACKMOL",
        executable=str(packmol),
        required=True,
    )

    status = inspect_tool(definition)

    assert status.available
    assert status.executable == str(packmol.resolve())
    assert "skipped" in status.diagnostic.lower()


def test_missing_required_tool_is_reported():
    definition = ToolDefinition(
        name="Missing test tool",
        executable="flexsolvmd-no-such-tool",
        required=True,
    )

    status = inspect_tool(definition)

    assert not status.available
    assert status.required
    assert status.error


def test_explicit_gromacs_path_can_be_resolved():
    path = GROMACS_PATHS["2024.5"]
    resolved = resolve_executable(path)

    # This assertion uses the configured path, not an assumption that
    # every developer machine has the same installation.
    if resolved is not None:
        assert resolved.endswith("/gmx")
