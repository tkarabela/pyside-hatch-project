import argparse
import logging
import shutil
import subprocess
import sys
import sysconfig
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from importlib.metadata import version
from pathlib import Path
from typing import Any, NoReturn, override

from hatchling.bridge.app import Application
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.plugin import hookimpl

__version__ = version("pyside-hatch-project")
HATCH_PLUGIN_NAME = "pyside-hatch-project"
logger = logging.getLogger(HATCH_PLUGIN_NAME)


def _traverse_dict(d: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        d = d.get(key, {})
    return d


def _ui_output_path(path: Path) -> Path:
    return path.with_name(f"ui_{path.stem}.py")


def _ts_output_path(path: Path) -> Path:
    return path.with_suffix(".qm")


def _qrc_output_path(path: Path) -> Path:
    return path.with_name(f"rc_{path.stem}.py")


@dataclass
class Config:
    files: list[Path] = field(default_factory=list)

    def add(self, files: Iterable[Path]) -> None:
        registered = set(self.files)

        for path in files:
            if path.suffix in (".ui", ".ts", ".qrc") and path not in registered:
                registered.add(path)
                self.files.append(path)

    @property
    def ui_files(self) -> Iterable[Path]:
        return (path for path in self.files if path.suffix == ".ui")

    @property
    def ts_files(self) -> Iterable[Path]:
        return (path for path in self.files if path.suffix == ".ts")

    @property
    def qrc_files(self) -> Iterable[Path]:
        return (path for path in self.files if path.suffix == ".qrc")


class Project:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.config = self.read_config(root)

    @staticmethod
    def read_config(root: Path) -> Config:
        config = Config()
        pyproject = tomllib.loads(root.joinpath("pyproject.toml").read_text(encoding="utf-8"))

        # [tool.pyside6-project]
        config.add(
            root.joinpath(relpath)
            for relpath in _traverse_dict(pyproject, ("tool", "pyside6-project")).get("files", [])
        )

        # [tool.pyside-hatch-project]
        # [tool.hatch.build.hooks.pyside-hatch-project]
        for toml_path in (
            ("tool", "pyside-hatch-project"),
            ("tool", "hatch", "build", "hooks", HATCH_PLUGIN_NAME),
        ):
            for attribute in ("ui_files", "ts_files", "qrc_files"):
                for relpath in _traverse_dict(pyproject, toml_path).get(attribute, []):
                    config.add(root.glob(relpath))

        return config

    def list_output_files(self) -> Iterable[Path]:
        yield from (_ui_output_path(path) for path in self.config.ui_files)
        yield from (_ts_output_path(path) for path in self.config.ts_files)
        yield from (_qrc_output_path(path) for path in self.config.qrc_files)

    def list_python_sources(self) -> Iterable[Path]:
        src_dir = self.root.joinpath("src")
        source_dir = src_dir if src_dir.exists() else self.root
        return (
            path
            for path in sorted(source_dir.rglob("*.py"))
            if not path.name.startswith(("ui_", "rc_")) and "__pycache__" not in path.parts
        )

    def compile_input_files(self) -> Iterable[Path]:
        if ui_files := list(self.config.ui_files):
            self.info(f"Compiling {len(ui_files)} .ui files")
            for path in ui_files:
                output_path = _ui_output_path(path)
                self.run_tool("pyside6-uic", path, "-o", output_path)
                yield output_path

        if ts_files := list(self.config.ts_files):
            self.info(f"Compiling {len(ts_files)} .ts files")
            for path in ts_files:
                output_path = _ts_output_path(path)
                self.run_tool("pyside6-lrelease", path, "-qm", output_path)
                yield output_path

        # compile .qrc files last, in case they reference compiled translations (.qm files)
        if qrc_files := list(self.config.qrc_files):
            self.info(f"Compiling {len(qrc_files)} .qrc files")
            for path in qrc_files:
                output_path = _qrc_output_path(path)
                self.run_tool("pyside6-rcc", path, "-o", output_path)
                yield output_path

    def clean_compiled_files(self) -> None:
        for path in self.list_output_files():
            path.unlink(missing_ok=True)

    def update_translations(self) -> None:
        if not (ts_files := list(self.config.ts_files)):
            return

        self.info(f"Updating {len(ts_files)} .ts files")

        input_paths = [*self.config.ui_files, *self.list_python_sources()]

        for ts in self.config.ts_files:
            self.run_tool("pyside6-lupdate", *input_paths, "-ts", ts)

    def run_tool(self, tool_name: str, *args: str | Path) -> None:
        # prefer tools installed alongside the running interpreter, but fall back to PATH: pip's isolated
        # build environment is not a venv, its scripts directory is only made available through PATH
        tool = shutil.which(tool_name, path=sysconfig.get_path("scripts")) or shutil.which(tool_name)
        if tool is None:
            self.fail(f"{tool_name} not found (is pyside6-essentials installed?)")
        cmd = [tool, *map(str, args)]
        self.debug(f"Running: {cmd}")
        rv = subprocess.run(cmd, check=False).returncode
        if rv != 0:
            self.fail(f"{' '.join(cmd)} failed with exit code {rv}")

    def info(self, msg: str) -> None:
        logger.info(msg)

    def debug(self, msg: str) -> None:
        logger.debug(msg)

    def fail(self, msg: str) -> NoReturn:
        logger.fatal(msg)
        raise RuntimeError(msg)


class HatchProject(Project):
    def __init__(self, hook: BuildHookInterface[Any]) -> None:
        self.hook = hook
        self.app: Application = hook.app
        super().__init__(root=Path(hook.root))

    @override
    def info(self, msg: str) -> None:
        self.app.display_info(msg)

    @override
    def debug(self, msg: str) -> None:
        self.app.display_debug(msg)

    @override
    def fail(self, msg: str) -> NoReturn:
        self.app.abort(msg)
        raise SystemExit(1)  # not used, Application.abort() is just missing NoReturn annotation


class PysideHatchProjectBuildHook(BuildHookInterface[Any]):
    PLUGIN_NAME = HATCH_PLUGIN_NAME

    @override
    def clean(self, versions: list[str]) -> None:
        self.__project.clean_compiled_files()

    @override
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        project = self.__project
        output_files = list(project.compile_input_files())
        # artifacts are gitignore-style patterns relative to the project root, anchored to match only these files
        build_data["artifacts"].extend(f"/{path.relative_to(project.root).as_posix()}" for path in output_files)

    @property
    def __project(self) -> HatchProject:
        return HatchProject(self)


class _Command(StrEnum):
    BUILD = "build"
    CLEAN = "clean"
    LUPDATE = "lupdate"


class CLI:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("command", choices=[_Command.BUILD, _Command.CLEAN, _Command.LUPDATE])
        self.parser.add_argument("-v", "--verbose", action="store_true", default=False)
        self.parser.add_argument("-V", "--version", action="version", version=__version__)

    def run(self, argv: list[str]) -> int:
        args = self.parser.parse_args(argv)
        command = _Command(args.command)
        verbose: bool = args.verbose

        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        project = Project(Path.cwd().resolve())

        try:
            match command:
                case _Command.BUILD:
                    _ = list(project.compile_input_files())
                case _Command.CLEAN:
                    project.clean_compiled_files()
                case _Command.LUPDATE:
                    project.update_translations()
            return 0
        except Exception:
            logger.exception("pyside-hatch-project failed")
            return 1


@hookimpl
def hatch_register_build_hook():
    return PysideHatchProjectBuildHook


def main() -> int:
    return CLI().run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
