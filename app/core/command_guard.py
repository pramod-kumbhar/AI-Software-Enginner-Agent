import re
import shlex
from pathlib import Path
from typing import List, Tuple, Optional
from app.core.logger import get_logger

logger = get_logger("command_guard")

class CommandGuard:
    """
    Subprocess Command Execution Security Guard & Allowlist Policy.
    Enforces tokenized execution, prevents shell injection, command chaining, and dangerous binaries.
    """

    ALLOWED_EXECUTABLES = {
        "pytest",
        "python",
        "python.exe",
        "git",
        "ruff"
    }

    ALLOWED_PYTHON_MODULES = {
        "pytest",
        "compileall",
        "unittest"
    }

    ALLOWED_GIT_SUBCOMMANDS = {
        "status",
        "diff",
        "log",
        "branch",
        "checkout",
        "add",
        "commit"
    }

    DANGEROUS_BINARIES = {
        "rm", "del", "erase", "format", "shutdown", "reboot",
        "powershell", "powershell.exe", "pwsh", "cmd", "cmd.exe",
        "bash", "sh", "zsh", "dash", "curl", "wget",
        "nc", "netcat", "ncat", "socat", "ssh", "scp", "sftp",
        "chmod", "chown", "sudo", "su", "docker", "kubectl"
    }

    SHELL_CHAINING_CHARACTERS = [";", "&&", "||", "|", "`", "$(", ">", ">>", "<", "&"]

    @classmethod
    def validate_command(
        cls,
        cmd: List[str] | str,
        cwd: Optional[str] = None,
        workspace_root: Optional[str] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates command safety before execution.
        Returns (is_valid, reason, tokenized_args).
        """
        if isinstance(cmd, str):
            # Check for shell injection / chaining characters in raw strings
            for char in cls.SHELL_CHAINING_CHARACTERS:
                if char in cmd:
                    logger.error(f"COMMAND INJECTION BLOCKED: Detected shell chaining character '{char}' in '{cmd}'")
                    return False, f"SHELL INJECTION DETECTED: Command contains prohibited chaining operator '{char}'.", []
            
            try:
                tokens = shlex.split(cmd, posix=False)
            except Exception as e:
                return False, f"Malformed command syntax: {str(e)}", []
        elif isinstance(cmd, list):
            tokens = list(cmd)
        else:
            return False, "Command must be a string or list of argument tokens.", []

        if not tokens:
            return False, "Empty command provided.", []

        executable = Path(tokens[0]).name.lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]

        # 1. Block dangerous binaries
        if executable in cls.DANGEROUS_BINARIES or tokens[0].lower() in cls.DANGEROUS_BINARIES:
            logger.error(f"DANGEROUS COMMAND BLOCKED: Binary '{executable}' is strictly prohibited.")
            return False, f"COMMAND EXECUTION BLOCKED: Binary '{executable}' is not permitted by security policy.", []

        # 2. Check allowlist
        if executable not in cls.ALLOWED_EXECUTABLES:
            logger.error(f"UNAUTHORIZED COMMAND BLOCKED: Executable '{executable}' is not in allowlist.")
            return False, f"COMMAND NOT PERMITTED: Executable '{executable}' is not authorized.", []

        # 3. Deep validation for python
        if executable == "python":
            if len(tokens) >= 3 and tokens[1] == "-m":
                mod = tokens[2].lower()
                if mod not in cls.ALLOWED_PYTHON_MODULES:
                    return False, f"UNAUTHORIZED PYTHON MODULE: Module '-m {mod}' is not permitted.", []

        # 4. Deep validation for git
        if executable == "git":
            if len(tokens) >= 2:
                git_sub = tokens[1].lower()
                if git_sub not in cls.ALLOWED_GIT_SUBCOMMANDS:
                    return False, f"UNAUTHORIZED GIT OPERATION: Subcommand 'git {git_sub}' requires explicit admin approval.", []
                # Block force flags
                for arg in tokens[2:]:
                    if arg in ["--force", "-f", "--hard"]:
                        return False, f"DANGEROUS GIT FLAG: Destructive flag '{arg}' is blocked.", []

        # 5. Validate working directory sandboxing if workspace root provided
        if cwd and workspace_root:
            cwd_path = Path(cwd).resolve()
            ws_path = Path(workspace_root).resolve()
            try:
                cwd_path.relative_to(ws_path)
            except ValueError:
                return False, f"SANDBOX VIOLATION: Execution directory '{cwd}' is outside workspace '{workspace_root}'.", []

        return True, "Command authorized by policy.", tokens

command_guard = CommandGuard()
