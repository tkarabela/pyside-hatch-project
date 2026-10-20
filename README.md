# pyside-hatch-project

A Hatch-friendly alternative to `pyside6-project` for managing UI files, resource files and translations.
This library provides a Hatchling plugin as well as stand-alone CLI tool, both called `pyside-hatch-project`.

What this library gives you over `pyside6-project`:
- Compile `.ui`/`.ts`/`.qrc` as part of a standard Python build, no extra steps needed.
- Specify paths to `.ui`/`.ts`/`.qrc` using glob patterns in `pyproject.toml`.

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

From the terminal, you can use the `pyside6-project` compatible commands:

```shell
pyside-hatch-project build    # compile .ui/.ts/.qrc files
pyside-hatch-project lupdate  # extract strings from .py/.ui files into .ts files
pyside-hatch-project clean    # remove compilation outputs (ui_*.py, rc_*.py, *.qm)
```

## License

MIT – see [LICENSE.txt](./LICENSE.txt).
