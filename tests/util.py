import subprocess
import sys
from pathlib import Path

DUMMY_PROJECT = Path(__file__).parent / "dummy_project"
REPO_ROOT = Path(__file__).parent.parent

# Paths relative to the dummy project root
UI_SOURCE = "src/dummy_app/main_window.ui"
TS_SOURCE = "src/dummy_app/translations/app_cs.ts"
QRC_SOURCE = "src/dummy_app/resources.qrc"
UI_OUTPUT = "src/dummy_app/ui_main_window.py"
QM_OUTPUT = "src/dummy_app/translations/app_cs.qm"
QRC_OUTPUT = "src/dummy_app/rc_resources.py"
OUTPUTS = (UI_OUTPUT, QM_OUTPUT, QRC_OUTPUT)

# The same outputs, as they appear inside a wheel
WHEEL_OUTPUTS = tuple(path.removeprefix("src/") for path in OUTPUTS)


def run_python(code: str, cwd: Path, *extra_path: Path) -> subprocess.CompletedProcess[str]:
    """Run a Python snippet in a fresh interpreter, with `extra_path` prepended to `sys.path`."""
    prelude = "".join(f"import sys; sys.path.insert(0, {str(p)!r})\n" for p in extra_path)
    return subprocess.run(
        [sys.executable, "-c", prelude + code],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
