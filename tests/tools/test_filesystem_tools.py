import pytest
import tempfile
from pathlib import Path
from app.tools.filesystem.handlers import FilesystemToolHandlers
from app.services.filesystem import SecurityViolationError

def test_filesystem_tools_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file
        create_res = FilesystemToolHandlers.create_file(
            file_path="app/config.py",
            content="DEBUG = True\n",
            workspace_root=tmpdir
        )
        assert create_res["created"] is True
        assert create_res["size_bytes"] > 0
        
        # File exists
        exists_res = FilesystemToolHandlers.file_exists("app/config.py", workspace_root=tmpdir)
        assert exists_res["exists"] is True
        
        # Read file
        read_res = FilesystemToolHandlers.read_file("app/config.py", workspace_root=tmpdir)
        assert "DEBUG = True" in read_res["content"]
        
        # Modify file
        mod_res = FilesystemToolHandlers.modify_file("app/config.py", "DEBUG = False\n", workspace_root=tmpdir)
        assert mod_res["created"] is True
        
        # Read modified
        read_mod = FilesystemToolHandlers.read_file("app/config.py", workspace_root=tmpdir)
        assert "DEBUG = False" in read_mod["content"]
        
        # List files
        list_res = FilesystemToolHandlers.list_files(workspace_root=tmpdir)
        assert "app/config.py" in list_res["files"]
        
        # Metadata
        meta = FilesystemToolHandlers.get_file_metadata("app/config.py", workspace_root=tmpdir)
        assert meta["is_file"] is True
        assert meta["size_bytes"] > 0

def test_filesystem_tools_path_traversal_shield():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(SecurityViolationError):
            FilesystemToolHandlers.read_file("../../etc/passwd", workspace_root=tmpdir)
            
        with pytest.raises(SecurityViolationError):
            FilesystemToolHandlers.create_file("../outside.txt", "attack", workspace_root=tmpdir)
