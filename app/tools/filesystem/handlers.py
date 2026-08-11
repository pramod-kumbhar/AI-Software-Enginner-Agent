import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.services.filesystem import FilesystemService, SecurityViolationError

class FilesystemToolHandlers:
    """
    Controlled filesystem operations operating strictly within a sandboxed project workspace.
    """
    
    @staticmethod
    def _get_service(workspace_root: Optional[str]) -> FilesystemService:
        root = workspace_root or "generated_projects/default"
        return FilesystemService(workspace_root=root)

    @classmethod
    def list_files(cls, workspace_root: Optional[str] = None, directory: str = "") -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        files = fs.list_directory(relative_dir=directory)
        return {
            "workspace_root": str(fs.workspace_root),
            "directory": directory,
            "total_files": len(files),
            "files": files
        }

    @classmethod
    def read_file(cls, file_path: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        success, content_or_err = fs.read_file(file_path)
        if not success:
            if "traversal" in content_or_err.lower():
                raise SecurityViolationError(content_or_err)
            raise FileNotFoundError(content_or_err)
        return {
            "file_path": file_path,
            "content": content_or_err,
            "size_bytes": len(content_or_err.encode("utf-8"))
        }

    @classmethod
    def file_exists(cls, file_path: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        try:
            target = fs._resolve_safe_path(file_path)
            exists = target.exists() and target.is_file()
            return {"file_path": file_path, "exists": exists}
        except SecurityViolationError:
            return {"file_path": file_path, "exists": False, "security_violation": True}

    @classmethod
    def create_file(cls, file_path: str, content: str, overwrite: bool = False, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        success, path_or_err = fs.write_file(file_path, content, overwrite=overwrite)
        if not success:
            if "traversal" in path_or_err.lower():
                raise SecurityViolationError(path_or_err)
            raise IOError(f"Could not create file '{file_path}': {path_or_err}")
        return {
            "file_path": file_path,
            "created": True,
            "absolute_path": path_or_err,
            "size_bytes": len(content.encode("utf-8"))
        }

    @classmethod
    def modify_file(cls, file_path: str, content: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        return cls.create_file(file_path=file_path, content=content, overwrite=True, workspace_root=workspace_root)

    @classmethod
    def create_directory(cls, directory: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        target = fs._resolve_safe_path(directory)
        target.mkdir(parents=True, exist_ok=True)
        return {
            "directory": directory,
            "created": True,
            "absolute_path": str(target)
        }

    @classmethod
    def get_file_metadata(cls, file_path: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        fs = cls._get_service(workspace_root)
        target = fs._resolve_safe_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        stat = target.stat()
        return {
            "file_path": file_path,
            "size_bytes": stat.st_size,
            "is_file": target.is_file(),
            "is_directory": target.is_dir(),
            "modified_time": stat.st_mtime
        }
