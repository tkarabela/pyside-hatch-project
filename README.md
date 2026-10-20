[![build master branch](https://img.shields.io/github/actions/workflow/status/tkarabela/pyside-hatch-project/ci.yml?branch=master)](https://github.com/tkarabela/pyside-hatch-project/actions)
[![test code coverage](https://img.shields.io/codecov/c/github/tkarabela/pyside-hatch-project)](https://app.codecov.io/github/tkarabela/pyside-hatch-project)
[![Static Badge](https://img.shields.io/badge/Pyrefly%20%26%20Ruff-checked-blue?style=flat)](https://github.com/tkarabela/pyside-hatch-project/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/pyside-hatch-project.svg?style=flat)](https://pypi.org/project/pyside-hatch-project/)
[![PyPI - Status](https://img.shields.io/pypi/status/pyside-hatch-project.svg?style=flat)](https://pypi.org/project/pyside-hatch-project/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyside-hatch-project.svg?style=flat)](https://pypi.org/project/pyside-hatch-project/)
[![PyPI - License](https://img.shields.io/pypi/l/pyside-hatch-project.svg?style=flat)](LICENSE.txt)

# pyside-hatch-project

A Hatch-friendly alternative to `pyside6-project` for managing UI files, resource files and translations.
This library provides a Hatchling plugin as well as stand-alone CLI tool, both called `pyside-hatch-project`.
It reimplements a subset of `pyside6-project` functionality.

What this library gives you over `pyside6-project`:
- Compile `.ui`/`.ts`/`.qrc` as part of a standard Python build, no extra steps needed.
- Specify paths to `.ui`/`.ts`/`.qrc` using glob patterns in `pyproject.toml`.

If you'd rather just call `pyside6-project` from Hatchling, there is a similar project that does this:
[hatch-pyside](https://github.com/s-ball/hatch-pyside).

## Usage

Example `pyproject.toml`:

```toml
[project]
name = "example-project"

[dependency-groups]
dev = [
    "pyside-hatch-project",
]

[build-system]
requires = ["hatchling>=1.27", "pyside-hatch-project"]
build-backend = "hatchling.build"

[tool.hatch.build.hooks.pyside-hatch-project]
ui_files = ["src/**/*.ui"]
ts_files = ["src/**/*.ts"]
qrc_files = ["src/**/*.qrc"]

# -- If you don't want to use the Hatchling plugin:
# [tool.pyside-hatch-project]
# ui_files = ["src/**/*.ui"]
# ts_files = ["src/**/*.ts"]
# qrc_files = ["src/**/*.qrc"]

# -- If you want to use standard pyside6-project definitions:
# [tool.hatch.build.hooks.pyside-hatch-project]
#
# [tool.pyside6-project]
# files = [
#     "src/main.py",
#     "src/my_widget.ui",
#     "src/my_translation.ts",
#     "src/my_resource.qrc",
# ]
```

From the terminal, you can use `pyside6-project` compatible commands:

```shell
pyside-hatch-project build    # compile .ui/.ts/.qrc files
pyside-hatch-project lupdate  # extract strings from .py/.ui files into .ts files
pyside-hatch-project clean    # remove compilation outputs (ui_*.py, rc_*.py, *.qm)
```

The compiled files can be `.gitignore`d - the build hook will add them as artifacts explicitly.

## Troubleshooting

**Qt tools fail with exit code 127 on Linux.** Qt's tools need some system libraries on Linux: GLib for all
of them (`uic`, `rcc`, `lrelease`, `lupdate`), plus Kerberos GSSAPI and Brotli for `lrelease`/`lupdate`.
Desktop installs and GitHub-hosted runners have them, but minimal container images such as `python:*-slim`
or `ubuntu:*` don't. Install them in the image, e.g. on Debian/Ubuntu:

```shell
apt-get install -y libglib2.0-0t64 libgssapi-krb5-2 libbrotli1   # libglib2.0-0 on older releases
```

## Development

```shell
uv sync
uv run pytest           # unit and integration tests
uv run pytest -m e2e    # end-to-end builds with pip and uv in fresh environments (slow, needs network)
uv run ruff check && uv run pyrefly check
```

## License

MIT – see [LICENSE.txt](./LICENSE.txt).
