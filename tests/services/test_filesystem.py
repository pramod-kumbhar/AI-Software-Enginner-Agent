import pytest
import tempfile
import os
from pathlib import Path
from app.services.filesystem import FilesystemService, SecurityViolationError

def test_filesystem_safe_write_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = FilesystemService(workspace_root=tmpdir)
        
        success, path = fs.write_file("app/main.py", "print('hello world')")
        assert success is True
        
        read_success, content = fs.read_file("app/main.py")
        assert read_success is True
        assert "print('hello world')" in content
        
        files = fs.list_directory()
        assert "app/main.py" in files

def test_filesystem_path_traversal_blocked():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = FilesystemService(workspace_root=tmpdir)
        
        with pytest.raises(SecurityViolationError):
            fs._resolve_safe_path("../../etc/passwd")
