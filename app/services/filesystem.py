import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class SecurityViolationError(Exception):
    """Raised when an operation attempts to breach workspace sandboxing."""
    pass

class FilesystemService:
    """
    Sandboxed filesystem manager restricting all I/O strictly to a dedicated project workspace.
    Guarantees path traversal prevention, protected file safety, symlink protection, and size limits.
    """
    PROTECTED_FILES = {".env", ".env.local", ".env.production", ".git", "id_rsa", "id_ed25519"}
    MAX_READ_FILE_SIZE = 10 * 1024 * 1024   # 10 MB limit
    MAX_WRITE_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit

    def __init__(self, workspace_root: Optional[str] = None, base_dir: Optional[str] = None):
        target_root = workspace_root or base_dir
        if target_root:
            self.workspace_root = Path(target_root).resolve()
        else:
            self.workspace_root = Path("generated_projects").resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolves relative path inside workspace, rejecting directory traversal and symlink escapes."""
        if not relative_path:
            return self.workspace_root

        # Reject absolute external paths and UNC paths
        if relative_path.startswith(("\\\\", "//")) or (len(relative_path) > 2 and relative_path[1] == ":"):
            raise SecurityViolationError(f"Absolute or UNC path forbidden: {relative_path}")

        clean_rel = relative_path.strip().lstrip("/\\")
        target = (self.workspace_root / clean_rel).resolve()
        
        # Verify target is strictly within workspace_root
        try:
            target.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityViolationError(f"Path traversal detected! Forbidden access to: {relative_path}")
            
        # Symlink Escape Check
        if target.is_symlink():
            resolved_symlink = target.resolve()
            try:
                resolved_symlink.relative_to(self.workspace_root)
            except ValueError:
                raise SecurityViolationError(f"Unsafe symlink escape detected: {relative_path}")

        return target

    def write_file(self, relative_path: str, content: str, overwrite: bool = True) -> Tuple[bool, str]:
        """Safely writes a file to the sandboxed workspace."""
        try:
            if len(content.encode("utf-8")) > self.MAX_WRITE_FILE_SIZE:
                return False, f"File size exceeds maximum allowed write limit ({self.MAX_WRITE_FILE_SIZE} bytes)."

            target_path = self._resolve_safe_path(relative_path)
            
            if target_path.name in self.PROTECTED_FILES and target_path.exists() and not overwrite:
                return False, f"Protected file '{target_path.name}' cannot be overwritten."
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return True, str(target_path)
        except Exception as e:
            return False, str(e)

    def read_file(self, relative_path: str) -> Tuple[bool, str]:
        """Safely reads a file from the sandboxed workspace."""
        try:
            target_path = self._resolve_safe_path(relative_path)
            if not target_path.exists():
                return False, f"File not found: {relative_path}"
                
            if target_path.stat().st_size > self.MAX_READ_FILE_SIZE:
                return False, f"File size exceeds maximum allowed read limit ({self.MAX_READ_FILE_SIZE} bytes)."

            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, str(e)

    def list_directory(self, relative_dir: str = "") -> List[str]:
        """Returns relative paths of all files inside workspace."""
        target_dir = self._resolve_safe_path(relative_dir)
        if not target_dir.exists():
            return []
            
        files_list = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.workspace_root)
                files_list.append(str(rel_path).replace("\\", "/"))
        return files_list

    def delete_workspace(self) -> bool:
        """Cleans up the entire workspace directory."""
        if self.workspace_root.exists():
            shutil.rmtree(self.workspace_root, ignore_errors=True)
            return True
        return False
