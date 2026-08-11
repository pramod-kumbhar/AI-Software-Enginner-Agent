import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.schemas.security import (
    SecurityFinding,
    SecuritySeverityEnum,
    SecurityCategoryEnum
)
from app.core.secret_scanner import secret_scanner
from app.core.prompt_guard import prompt_guard
from app.core.logger import get_logger

logger = get_logger("code_security_scanner")

class CodeSecurityScanner:
    """
    Static Application Security Testing (SAST) and Dependency Vulnerability Scanner.
    Inspects Python code, configuration files, and dependency manifests for vulnerabilities.
    """

    CODE_VULNERABILITY_RULES = [
        (
            r"\b(eval|exec)\s*\(",
            SecuritySeverityEnum.CRITICAL,
            SecurityCategoryEnum.CODE_SECURITY,
            "Arbitrary Code Execution via eval/exec",
            "Use of dynamic evaluation (eval/exec) allows arbitrary code execution.",
            "Replace dynamic evaluation with safe parsers (e.g., ast.literal_eval or json.loads)."
        ),
        (
            r"\bos\.system\s*\(",
            SecuritySeverityEnum.HIGH,
            SecurityCategoryEnum.COMMAND_EXECUTION,
            "Insecure os.system Call",
            "os.system executes commands via shell and is vulnerable to command injection.",
            "Use subprocess with structured argument list and shell=False."
        ),
        (
            r"\bsubprocess\.(?:Popen|run|call)\s*\([^)]*shell\s*=\s*True",
            SecuritySeverityEnum.CRITICAL,
            SecurityCategoryEnum.COMMAND_EXECUTION,
            "Command Injection Vulnerability (shell=True)",
            "Executing subprocesses with shell=True allows shell injection attacks.",
            "Pass arguments as a list and set shell=False."
        ),
        (
            r"f[\"'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*\{",
            SecuritySeverityEnum.HIGH,
            SecurityCategoryEnum.CODE_SECURITY,
            "Potential SQL Injection (String Interpolation)",
            "SQL query is constructed using string interpolation instead of parameterized queries.",
            "Use ORM query builders or parameterized placeholders."
        ),
        (
            r"\bpickle\.(?:loads|load)\s*\(",
            SecuritySeverityEnum.HIGH,
            SecurityCategoryEnum.CODE_SECURITY,
            "Insecure Deserialization (pickle)",
            "Unpickling untrusted data can lead to arbitrary code execution.",
            "Use safe serialization formats like JSON or Protocol Buffers."
        ),
        (
            r"\ballow_origins\s*=\s*\[[\"']\*[\"']\]",
            SecuritySeverityEnum.MEDIUM,
            SecurityCategoryEnum.API_SECURITY,
            "Overly Permissive CORS Policy",
            "CORS allows wildcard '*' origins on sensitive API endpoints.",
            "Restrict allowed origins to trusted domain names."
        )
    ]

    @classmethod
    def scan_directory(cls, workspace_path: str) -> List[SecurityFinding]:
        """Recursively scans all files in the workspace directory."""
        findings: List[SecurityFinding] = []
        root = Path(workspace_path)
        if not root.exists():
            return findings

        for file_path in root.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(root)).replace("\\", "/")
                # Skip virtual environments and git dirs
                if any(skip in rel_path for skip in [".git", "venv", "__pycache__", ".pytest_cache"]):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # 1. Scan for hardcoded credentials
                    secret_findings = secret_scanner.scan_text(content, file_path=rel_path)
                    findings.extend(secret_findings)

                    # 2. Scan for prompt injection in comments / README
                    if rel_path.endswith((".md", ".txt", ".py")):
                        source_type = "README" if "readme" in rel_path.lower() else "SOURCE_COMMENTS"
                        pi_res = prompt_guard.scan_content(content, source=source_type)
                        if pi_res["detected"]:
                            findings.append(SecurityFinding(
                                finding_id=f"sec_pi_{len(findings)+1}",
                                category=SecurityCategoryEnum.PROMPT_INJECTION,
                                severity=pi_res["risk_level"],
                                title="Prompt Injection Pattern Detected in File",
                                description=f"Adversarial instruction detected in {rel_path}: {', '.join(pi_res['indicators'])}",
                                source="PROMPT_GUARD",
                                file_path=rel_path,
                                impact="Agent manipulation, unauthorized command execution.",
                                recommendation="Neutralize untrusted text and tag as passive data.",
                                auto_fixable=True,
                                status="OPEN"
                            ))

                    # 3. SAST Rule Scanning on Python files
                    if rel_path.endswith(".py"):
                        cls._scan_code_rules(content, rel_path, findings)

                    # 4. Dependency checks
                    if rel_path in ["requirements.txt", "pyproject.toml"]:
                        cls._scan_dependencies(content, rel_path, findings)

                except Exception as e:
                    logger.error(f"Error scanning file {rel_path}: {str(e)}")

        return findings

    @classmethod
    def _scan_code_rules(cls, content: str, rel_path: str, findings: List[SecurityFinding]):
        """Evaluates SAST vulnerability regex rules against source code."""
        for pattern, severity, category, title, desc, rec in cls.CODE_VULNERABILITY_RULES:
            for m in re.finditer(pattern, content):
                line_num = content[:m.start()].count('\n') + 1
                findings.append(SecurityFinding(
                    finding_id=f"sec_code_{len(findings)+1}",
                    category=category,
                    severity=severity,
                    title=title,
                    description=desc,
                    source="STATIC_ANALYSIS",
                    file_path=rel_path,
                    line_number=line_num,
                    evidence=m.group(0),
                    impact="Security compromise, remote code execution or injection.",
                    recommendation=rec,
                    auto_fixable=(category == SecurityCategoryEnum.COMMAND_EXECUTION and "shell=True" in m.group(0)),
                    status="OPEN"
                ))

    @classmethod
    def _scan_dependencies(cls, content: str, rel_path: str, findings: List[SecurityFinding]):
        """Inspects package dependencies for unpinned versions or wildcard requirements."""
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue

            # Check for unpinned requirements (e.g. "requests" without ==)
            if rel_path == "requirements.txt" and not any(op in clean_line for op in ["==", ">=", "<=", "~="]):
                findings.append(SecurityFinding(
                    finding_id=f"sec_dep_{len(findings)+1}",
                    category=SecurityCategoryEnum.DEPENDENCIES,
                    severity=SecuritySeverityEnum.LOW,
                    title=f"Unpinned Dependency Version: {clean_line}",
                    description="Dependency version is unpinned, which exposes builds to supply-chain drift.",
                    source="DEPENDENCY_CHECK",
                    file_path=rel_path,
                    line_number=idx,
                    impact="Supply chain vulnerability, breaking API changes.",
                    recommendation="Pin exact package versions using 'package==x.y.z'.",
                    auto_fixable=True,
                    status="OPEN"
                ))

code_security_scanner = CodeSecurityScanner()
