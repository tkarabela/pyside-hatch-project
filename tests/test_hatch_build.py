import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from tests.util import OUTPUTS, QRC_SOURCE, TS_SOURCE, UI_SOURCE, WHEEL_OUTPUTS, run_python


def _build(project: Path, kind: str, dist: Path) -> Path:
    """Build a distribution through the PEP 517 interface, in the current environment (no isolation)."""
    result = run_python(
        f"import hatchling.build; print(hatchling.build.build_{kind}({str(dist)!r}))",
        project,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return dist / result.stdout.strip().splitlines()[-1]


def _wheel_contents(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as zf:
        return set(zf.namelist())


def test_wheel_contains_compiled_files(dummy_project: Path, tmp_path: Path) -> None:
    # The outputs are listed in the project's .gitignore, so they are only included if the hook registers them
    wheel = _build(dummy_project, "wheel", tmp_path / "dist")

    contents = _wheel_contents(wheel)
    for relpath in WHEEL_OUTPUTS:
        assert relpath in contents, relpath


def test_sdist_contains_sources_and_compiled_files(dummy_project: Path, tmp_path: Path) -> None:
    sdist = _build(dummy_project, "sdist", tmp_path / "dist")

    with tarfile.open(sdist) as tf:
        contents = {name.split("/", 1)[1] for name in tf.getnames() if "/" in name}
    for relpath in (UI_SOURCE, TS_SOURCE, QRC_SOURCE, *OUTPUTS):
        assert relpath in contents, relpath


def test_wheel_from_sdist(dummy_project: Path, tmp_path: Path) -> None:
    # This is what `uv build` / `python -m build` do by default
    sdist = _build(dummy_project, "sdist", tmp_path / "dist")
    with tarfile.open(sdist) as tf:
        tf.extractall(tmp_path / "unpacked", filter="data")
    (unpacked_project,) = (tmp_path / "unpacked").iterdir()

    wheel = _build(unpacked_project, "wheel", tmp_path / "dist")

    contents = _wheel_contents(wheel)
    for relpath in WHEEL_OUTPUTS:
        assert relpath in contents, relpath


def test_hatchling_clean(dummy_project: Path) -> None:
    def hatchling_build(*args: str) -> None:
        cmd = [sys.executable, "-m", "hatchling", "build", "-t", "wheel", *args]
        subprocess.run(cmd, cwd=dummy_project, check=True)

    hatchling_build("--hooks-only")
    for relpath in OUTPUTS:
        assert (dummy_project / relpath).exists(), relpath

    hatchling_build("--clean-only")
    for relpath in OUTPUTS:
        assert not (dummy_project / relpath).exists(), relpath
