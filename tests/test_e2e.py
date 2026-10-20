import os
import shutil
import subprocess
import venv
import zipfile
from pathlib import Path

import pytest

from tests.util import REPO_ROOT, WHEEL_OUTPUTS

pytestmark = pytest.mark.e2e


@pytest.fixture
def clean_python(tmp_path: Path) -> Path:
    """Interpreter of a fresh virtual environment, without PySide6 or this plugin installed."""
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    if os.name == "nt":
        return env_dir / "Scripts" / "python.exe"
    return env_dir / "bin" / "python"


@pytest.fixture
def isolated_project(clean_python: Path, dummy_project: Path, tmp_path: Path) -> Path:
    """Dummy project whose build-system requires the plugin wheel built from this checkout."""
    plugin_dist = tmp_path / "plugin_dist"
    _pip_wheel(clean_python, REPO_ROOT, plugin_dist)
    (plugin_wheel,) = plugin_dist.glob("pyside_hatch_project-*.whl")

    pyproject = dummy_project / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    requirement = f'"pyside-hatch-project @ {plugin_wheel.as_uri()}"'
    pyproject.write_text(text.replace('"pyside-hatch-project"', requirement), encoding="utf-8")
    return dummy_project


def _pip_wheel(python: Path, project: Path, dist: Path) -> None:
    cmd = [str(python), "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(dist), str(project)]
    subprocess.run(cmd, check=True)


def _assert_wheel_contains_outputs(dist: Path) -> None:
    (wheel,) = dist.glob("dummy_app-*.whl")
    with zipfile.ZipFile(wheel) as zf:
        contents = set(zf.namelist())
    for relpath in WHEEL_OUTPUTS:
        assert relpath in contents, relpath


def test_pip_wheel(clean_python: Path, isolated_project: Path, tmp_path: Path) -> None:
    # pip's isolated build environment is not a venv, the PySide6 tools are only reachable through PATH
    dist = tmp_path / "dist"
    _pip_wheel(clean_python, isolated_project, dist)
    _assert_wheel_contains_outputs(dist)


def test_uv_build(isolated_project: Path, tmp_path: Path) -> None:
    # uv builds the sdist first and the wheel from the unpacked sdist, each in a fresh venv
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv not found")
    dist = tmp_path / "dist"
    subprocess.run([uv, "build", "--no-cache", "--out-dir", str(dist), str(isolated_project)], check=True)
    _assert_wheel_contains_outputs(dist)
