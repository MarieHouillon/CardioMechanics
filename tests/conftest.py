import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate golden references instead of asserting against them.",
    )


@pytest.fixture(scope="session")
def update_golden(request):
    return request.config.getoption("--update-golden")


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def cm_env():
    """Environment for every binary invocation.

    kaRootDir must be set: the binaries resolve their bundled data files relative
    to it at runtime and segfault (getenv returns NULL) when it is unset. The
    CMake presets only set kaRootDir at build time, so a plain shell does not
    have it. OMP_NUM_THREADS=1 keeps serial runs deterministic.
    """
    env = os.environ.copy()
    env["kaRootDir"] = str(REPO_ROOT)
    env["OMP_NUM_THREADS"] = "1"
    return env


def _find_binary(name):
    override = os.environ.get("CM_BIN_DIR")
    if override:
        cand = Path(override) / name
        if cand.is_file():
            return cand
        raise FileNotFoundError(f"CM_BIN_DIR={override} set but {name} not found there")
    matches = [
        p
        for p in REPO_ROOT.glob(f"_build/*/bin/**/{name}")
        if p.is_file() and os.access(p, os.X_OK)
    ]
    if not matches:
        raise FileNotFoundError(
            f"{name} not found. Searched $CM_BIN_DIR and "
            f"{REPO_ROOT}/_build/*/bin/**/{name} — build the project first."
        )
    return max(matches, key=lambda p: p.stat().st_mtime)


@pytest.fixture(scope="session")
def binary():
    """Return a resolver: binary('CellModelTest') -> Path to the newest build."""
    return _find_binary
