import pytest
from app.services.filesystem import FilesystemService, SecurityViolationError

def test_relative_path_traversal_blocked(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    
    with pytest.raises(SecurityViolationError):
        fs._resolve_safe_path("../../.env")

    ok_read, read_err = fs.read_file("../../.env")
    assert ok_read is False
    assert "traversal" in read_err.lower() or "forbidden" in read_err.lower()

    ok_write, write_err = fs.write_file("../../../etc/passwd", "malicious_content")
    assert ok_write is False

def test_windows_drive_escape_blocked(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    
    with pytest.raises(SecurityViolationError):
        fs._resolve_safe_path("C:/Windows/System32/drivers/etc/hosts")

    ok, err = fs.read_file("C:/Windows/System32/drivers/etc/hosts")
    assert ok is False


def test_safe_workspace_write_and_read(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    write_ok, path = fs.write_file("app/main.py", "print('Hello Safe World')")
    assert write_ok is True
    
    read_ok, content = fs.read_file("app/main.py")
    assert read_ok is True
    assert content == "print('Hello Safe World')"
