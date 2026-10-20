from pathlib import Path

import pytest

from pyside_hatch_project import CLI, Project, __version__
from tests.util import OUTPUTS, QM_OUTPUT, QRC_OUTPUT, TS_SOURCE, UI_OUTPUT, UI_SOURCE, run_python


@pytest.fixture
def cli(dummy_project: Path, monkeypatch: pytest.MonkeyPatch) -> CLI:
    monkeypatch.chdir(dummy_project)
    return CLI()


def test_build(dummy_project: Path, cli: CLI) -> None:
    # The fresh copy has no .qm file, so rcc only succeeds if .ts files are compiled before .qrc files
    assert not (dummy_project / QM_OUTPUT).exists()

    assert cli.run(["build"]) == 0

    for relpath in OUTPUTS:
        assert (dummy_project / relpath).stat().st_size > 0, relpath

    ui_code = (dummy_project / UI_OUTPUT).read_text(encoding="utf-8")
    assert "class Ui_MainWindow" in ui_code
    compile(ui_code, UI_OUTPUT, "exec")

    rc_code = (dummy_project / QRC_OUTPUT).read_text(encoding="utf-8")
    compile(rc_code, QRC_OUTPUT, "exec")


def test_build_embeds_translation_in_resources(dummy_project: Path, cli: CLI) -> None:
    assert cli.run(["build"]) == 0

    result = run_python(
        """
from PySide6.QtCore import QFile, QTranslator
import dummy_app.rc_resources

assert QFile.exists(":/translations/app_cs.qm"), "qm file missing from resources"
translator = QTranslator()
assert translator.load(":/translations/app_cs.qm"), "failed to load translation"
print(translator.translate("MainWindow", "Hello"))
""",
        dummy_project,
        dummy_project / "src",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Ahoj"


def test_clean(dummy_project: Path, cli: CLI) -> None:
    sources = sorted(p for p in dummy_project.rglob("*") if p.is_file())
    assert cli.run(["build"]) == 0

    assert cli.run(["clean"]) == 0

    assert sorted(p for p in dummy_project.rglob("*") if p.is_file()) == sources


def test_clean_without_outputs(cli: CLI) -> None:
    assert cli.run(["clean"]) == 0


def test_lupdate(dummy_project: Path, cli: CLI) -> None:
    ts_path = dummy_project / TS_SOURCE

    assert cli.run(["lupdate"]) == 0

    ts = ts_path.read_text(encoding="utf-8")
    assert "<source>Window title from Python</source>" in ts
    assert "main_window.py" in ts
    assert "main_window.ui" in ts
    assert "<translation>Ahoj</translation>" in ts


def test_build_failure(dummy_project: Path, cli: CLI) -> None:
    (dummy_project / UI_SOURCE).write_text("<ui>this is not a valid form", encoding="utf-8")

    assert cli.run(["build"]) == 1


def test_missing_tool(dummy_project: Path) -> None:
    with pytest.raises(RuntimeError, match="not found"):
        Project(dummy_project).run_tool("pyside6-this-tool-does-not-exist")


def test_version(cli: CLI, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.run(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__
