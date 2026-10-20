import shutil
from pathlib import Path

import pytest

from tests.util import DUMMY_PROJECT


@pytest.fixture
def dummy_project(tmp_path: Path) -> Path:
    """Fresh copy of the dummy project, so that compiled outputs never land in the repository."""
    root = tmp_path / "dummy_project"
    shutil.copytree(DUMMY_PROJECT, root)
    return root
