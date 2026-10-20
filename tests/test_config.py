from pathlib import Path

from pyside_hatch_project import Project
from tests.util import (
    QM_OUTPUT,
    QRC_OUTPUT,
    QRC_SOURCE,
    TS_SOURCE,
    UI_OUTPUT,
    UI_SOURCE,
)


def _make_project(root: Path, pyproject: str, files: list[str]) -> Project:
    root.joinpath("pyproject.toml").write_text(pyproject, encoding="utf-8")
    for relpath in files:
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return Project(root)


def test_hatch_hook_table_with_globs(dummy_project: Path) -> None:
    project = Project(dummy_project)

    assert project.config.files == [dummy_project / UI_SOURCE, dummy_project / TS_SOURCE, dummy_project / QRC_SOURCE]
    assert list(project.config.ui_files) == [dummy_project / UI_SOURCE]
    assert list(project.config.ts_files) == [dummy_project / TS_SOURCE]
    assert list(project.config.qrc_files) == [dummy_project / QRC_SOURCE]


def test_standalone_table(tmp_path: Path) -> None:
    project = _make_project(
        tmp_path,
        """
        [tool.pyside-hatch-project]
        ui_files = ["forms/*.ui"]
        """,
        ["forms/a.ui", "forms/b.ui", "forms/nested/c.ui"],
    )

    assert sorted(project.config.files) == [tmp_path / "forms/a.ui", tmp_path / "forms/b.ui"]


def test_pyside6_project_table(tmp_path: Path) -> None:
    project = _make_project(
        tmp_path,
        """
        [tool.pyside6-project]
        files = ["main.py", "form.ui", "app_cs.ts", "res.qrc"]
        """,
        ["main.py", "form.ui", "app_cs.ts", "res.qrc"],
    )

    # .py files are part of a pyside6-project definition, but there is nothing to compile
    assert project.config.files == [tmp_path / "form.ui", tmp_path / "app_cs.ts", tmp_path / "res.qrc"]


def test_all_tables_are_merged_without_duplicates(tmp_path: Path) -> None:
    project = _make_project(
        tmp_path,
        """
        [tool.pyside6-project]
        files = ["a.ui"]

        [tool.pyside-hatch-project]
        ui_files = ["*.ui"]
        qrc_files = ["*.qrc"]

        [tool.hatch.build.hooks.pyside-hatch-project]
        ui_files = ["a.ui", "b.ui"]
        ts_files = ["*.ts"]
        """,
        ["a.ui", "b.ui", "x.ts", "y.qrc"],
    )

    files = project.config.files
    assert len(files) == len(set(files))
    assert set(files) == {tmp_path / name for name in ("a.ui", "b.ui", "x.ts", "y.qrc")}
    assert files[0] == tmp_path / "a.ui"


def test_unsupported_suffixes_are_ignored(tmp_path: Path) -> None:
    project = _make_project(
        tmp_path,
        """
        [tool.pyside-hatch-project]
        ui_files = ["*"]
        """,
        ["a.ui", "b.txt", "c.py"],
    )

    assert project.config.files == [tmp_path / "a.ui"]


def test_no_configuration(tmp_path: Path) -> None:
    project = _make_project(tmp_path, '[project]\nname = "x"\n', ["a.ui"])

    assert project.config.files == []
    assert list(project.list_output_files()) == []


def test_output_file_names(dummy_project: Path) -> None:
    project = Project(dummy_project)

    assert list(project.list_output_files()) == [
        dummy_project / UI_OUTPUT,
        dummy_project / QM_OUTPUT,
        dummy_project / QRC_OUTPUT,
    ]


def test_python_sources_prefer_src_and_skip_generated(tmp_path: Path) -> None:
    project = _make_project(
        tmp_path,
        "",
        [
            "setup_helper.py",
            "src/pkg/__init__.py",
            "src/pkg/widget.py",
            "src/pkg/ui_widget.py",
            "src/pkg/rc_resources.py",
            "src/pkg/__pycache__/widget.py",
        ],
    )

    assert list(project.list_python_sources()) == [tmp_path / "src/pkg/__init__.py", tmp_path / "src/pkg/widget.py"]


def test_python_sources_without_src(tmp_path: Path) -> None:
    project = _make_project(tmp_path, "", ["app.py", "pkg/view.py", "pkg/ui_view.py"])

    assert list(project.list_python_sources()) == [tmp_path / "app.py", tmp_path / "pkg/view.py"]
