from flexsolvmd.gromacs import GromacsInstallation


def test_installations_have_expected_paths():
    installation = GromacsInstallation(
        "2024.5",
        "/home/apandey/miniforge3/envs/"
        "gmx24.5/bin.AVX2_256/gmx",
        "gmx24.5",
    )

    assert installation.conda_env == "gmx24.5"
