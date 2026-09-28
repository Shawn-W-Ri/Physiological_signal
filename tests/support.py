"""Workspace-scoped temporary directories, including restricted Windows runners."""
from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid

@contextmanager
def temp_directory():
    root=(Path(__file__).resolve().parents[1]/'.test-tmp').resolve()
    root.mkdir(exist_ok=True)
    path=root/uuid.uuid4().hex
    path.mkdir()
    try:
        yield str(path)
    finally:
        # Only remove the test-owned child of this known workspace directory.
        if path.resolve().parent != root: raise ValueError('Invalid test cleanup path')
        shutil.rmtree(path)
