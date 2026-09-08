import sys, os
import pytest
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

@pytest.fixture(autouse=True, scope="session")
def add_project_root_to_path():
    """Ensure the project root is on ``sys.path`` for all test modules.
    This allows imports such as ``from core.reloj_fen import ...`` without
    having to modify each test file individually.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
