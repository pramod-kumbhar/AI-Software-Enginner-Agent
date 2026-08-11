import re
from typing import Dict, Any, List, Tuple
from app.schemas.security import SecuritySeverityEnum, SecurityCategoryEnum, SecurityFinding
from app.core.logger import get_logger

logger = get_logger("secret_scanner")

class SecretScanner:
    """
    High-precision secret detection and zero-leakage masking engine.
    Scans files, diffs, logs, tool parameters, and LLM payloads for hardcoded credentials.
    """

    SECRET_PATTERNS = {
        "GITHUB_PAT": (
            r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}|gho_[a-zA-Z0-9]{36})\b",
            SecuritySeverityEnum.CRITICAL,
            "GitHub Personal Access Token"
        ),
        "AWS_ACCESS_KEY": (
            r"\b(AKIA[0-9A-Z]{16})\b",
            SecuritySeverityEnum.CRITICAL,
            "AWS Access Key ID"
        ),
        "AWS_SECRET_KEY": (
            r"(?i)\b(aws_secret_access_key|aws_secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?\b",
            SecuritySeverityEnum.CRITICAL,
            "AWS Secret Access Key"
        ),
        "PRIVATE_KEY": (
            r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE\s+KEY-----",
            SecuritySeverityEnum.CRITICAL,
            "Asymmetric Private Key"
        ),
        "JWT_TOKEN": (
            r"\b(ey[A-Za-z0-9-_]{10,}\.ey[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_.+/=]{10,})\b",
            SecuritySeverityEnum.HIGH,
            "JSON Web Token (JWT)"
        ),
        "DATABASE_URL": (
            r"\b(postgres(?:ql)?|mongodb(?:\+srv)?|mysql|redis)://[a-zA-Z0-9_\.\-]+:[^\s@\"']+@[a-zA-Z0-9_\.\-]+(?::\d+)?/[a-zA-Z0-9_\.\-]+\b",
            SecuritySeverityEnum.CRITICAL,
            "Database Connection URI with Credentials"
        ),
        "BEARER_TOKEN": (
            r"(?i)\bBearer\s+([a-zA-Z0-9_\-\.]{24,})\b",
            SecuritySeverityEnum.HIGH,
            "Authorization Bearer Token"
        ),
        "GENERIC_SECRET_ASSIGNMENT": (
            r"(?i)\b(api_key|apikey|secret_key|client_secret|auth_token|db_password|db_pass|password|secret)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\$]{16,})['\"]",
            SecuritySeverityEnum.HIGH,
            "Hardcoded API Key / Password Assignment"
        )
    }

    @classmethod
    def scan_text(cls, text: str, file_path: str = "memory_buffer") -> List[SecurityFinding]:
        """Scans arbitrary text for hardcoded credentials and returns SecurityFinding items."""
        if not text or not isinstance(text, str):
            return []

        findings: List[SecurityFinding] = []

        for name, (pattern, severity, desc) in cls.SECRET_PATTERNS.items():
            matches = list(re.finditer(pattern, text))
            for m in matches:
                matched_str = m.group(0)
                # Avoid false positives on common placeholders
                if any(ph in matched_str.lower() for ph in ["example", "placeholder", "your_secret", "dummy_token", "test_key_0000000000000000"]):
                    continue

                line_num = text[:m.start()].count('\n') + 1
                finding = SecurityFinding(
                    finding_id=f"sec_sec_{name.lower()}_{line_num}",
                    category=SecurityCategoryEnum.SECRETS,
                    severity=severity,
                    title=f"Hardcoded Secret Detected: {desc}",
                    description=f"Found potential unmasked credential pattern ({desc}) at line {line_num}.",
                    source="SECRET_SCANNER",
                    file_path=file_path,
                    line_number=line_num,
                    evidence=cls.mask_secret(matched_str),
                    impact="Credential theft, unauthorized API access, and repository leakage.",
                    recommendation="Remove hardcoded secret and load from environment variables / secret manager.",
                    auto_fixable=True,
                    approval_required=False,
                    status="OPEN"
                )
                findings.append(finding)

        if findings:
            logger.warning(f"SECRET SCANNER: Detected {len(findings)} exposed secrets in {file_path}")
        return findings

    @classmethod
    def mask_secret(cls, text: str) -> str:
        """
        Masks exposed credentials from string for safe logging and UI display.
        Example: ghp_123456789012345678901234567890123456 -> ghp_************************************
        """
        if not text or not isinstance(text, str):
            return ""

        masked = text
        for name, (pattern, _, _) in cls.SECRET_PATTERNS.items():
            def repl(m):
                full_val = m.group(0)
                if len(full_val) <= 8:
                    return "********"
                prefix = full_val[:4]
                suffix = full_val[-2:] if len(full_val) > 12 else ""
                masked_len = len(full_val) - len(prefix) - len(suffix)
                return f"{prefix}{'*' * masked_len}{suffix}"
            
            masked = re.sub(pattern, repl, masked)
        return masked

secret_scanner = SecretScanner()
