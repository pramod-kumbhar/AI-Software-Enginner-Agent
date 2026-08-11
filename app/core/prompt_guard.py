import re
import base64
from typing import Dict, Any, List, Tuple, Optional
from app.schemas.security import SecuritySeverityEnum, SecurityCategoryEnum
from app.core.logger import get_logger

logger = get_logger("prompt_guard")

class PromptInjectionGuard:
    """
    Multi-layered deterministic Prompt Injection & Jailbreak Defense Engine.
    Evaluates untrusted inputs, CI logs, README files, commit messages, and tool outputs.
    """
    
    # 1. System Prompt Override & Jailbreak Patterns
    OVERRIDE_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts|rules|commands)\b",
        r"(?i)\bdisregard\s+(all\s+)?(previous|prior|system)\s+(instructions|directives)\b",
        r"(?i)\b(forget|override|bypass)\s+(all\s+)?(rules|safety|guidelines|policies)\b",
        r"(?i)\byou\s+are\s+now\s+(unrestricted|in\s+god\s+mode|dan|jailbroken|an\s+unconstrained\s+ai)\b",
        r"(?i)\bnew\s+system\s+prompt\s*:\b",
        r"(?i)\[system\s+override\]",
        r"(?i)---+\s*end\s+of\s+system\s+prompt\s*---+"
    ]

    # 2. Secret Exfiltration & Credential Theft Patterns
    EXFILTRATION_PATTERNS = [
        r"(?i)\b(reveal|print|dump|read|display|send|upload|exfiltrate)\s+(\.env|secrets|api_key|token|password|credentials|private_key|aws_secret)\b",
        r"(?i)\bcat\s+(\.env|\.aws/credentials|\.ssh/id_rsa)\b",
        r"(?i)\b(send|post|curl|wget)\s+.*(api_key|token|password|secret)\s+to\b",
        r"(?i)\b(echo|printenv|env)\b.*(secret|token|key|password)"
    ]

    # 3. Unauthorized Action & Policy Bypass Patterns
    DANGEROUS_ACTION_PATTERNS = [
        r"(?i)\b(disable|bypass|turn\s+off|skip)\s+(security|checks|approval|validation|qa|lint)\b",
        r"(?i)\b(approve|force)\s+(deployment|release|merge|production)\s+without\s+approval\b",
        r"(?i)\bgit\s+push\s+(--force|-f)\b",
        r"(?i)\b(rm\s+-rf|del\s+/f|format\s+[c-z]:|shutdown)\b",
        r"(?i)\b(powershell|bash|sh|cmd\.exe|curl|wget)\s+-[a-zA-Z]*e\b"
    ]

    # Untrusted Source Categories
    UNTRUSTED_SOURCES = {
        "UNTRUSTED_CONTENT",
        "CI_LOGS",
        "README",
        "SOURCE_COMMENTS",
        "GITHUB_ISSUES",
        "GITHUB_PR_COMMENTS",
        "COMMIT_MESSAGES",
        "TEST_OUTPUT",
        "DEPLOYMENT_LOGS",
        "EXTERNAL_API",
        "TOOL_OUTPUT",
        "REPOSITORY_DOCUMENTATION"
    }

    @classmethod
    def scan_content(
        cls,
        content: str,
        source: str = "UNTRUSTED_CONTENT",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scans content for prompt injection, jailbreak attempts, and dangerous instructions.
        Returns risk evaluation, detected indicators, sanitized content, and deterministic action.
        """
        if not content or not isinstance(content, str):
            return {
                "detected": False,
                "risk_level": SecuritySeverityEnum.INFO,
                "indicators": [],
                "sanitized_content": "",
                "recommended_action": "ALLOW",
                "is_blocked": False
            }

        indicators: List[str] = []
        is_untrusted_source = source.upper() in cls.UNTRUSTED_SOURCES

        # 1. Regex Pattern Matching
        for pattern in cls.OVERRIDE_PATTERNS:
            if re.search(pattern, content):
                indicators.append(f"Prompt Override Pattern Detected: '{pattern}'")

        for pattern in cls.EXFILTRATION_PATTERNS:
            if re.search(pattern, content):
                indicators.append(f"Secret Exfiltration Pattern Detected: '{pattern}'")

        for pattern in cls.DANGEROUS_ACTION_PATTERNS:
            if re.search(pattern, content):
                indicators.append(f"Dangerous Action Request Pattern Detected: '{pattern}'")

        # 2. Hidden / Obfuscated Payload Detection (Base64 decodable dangerous phrases)
        cls._check_obfuscated_payloads(content, indicators)

        # 3. Delimiter Injection Check
        if "<SYSTEM_OVERRIDE>" in content or "[SYSTEM_INSTRUCTION]" in content:
            indicators.append("System Delimiter Injection Detected")

        # Determine Severity and Action
        detected = len(indicators) > 0
        if not detected:
            return {
                "detected": False,
                "risk_level": SecuritySeverityEnum.LOW,
                "indicators": [],
                "sanitized_content": cls._wrap_as_inert_data(content, source),
                "recommended_action": "ALLOW",
                "is_blocked": False
            }

        # If any high/critical indicators are present
        has_critical = any(
            "Secret Exfiltration" in ind or "Prompt Override" in ind or "Dangerous Action" in ind
            for ind in indicators
        )

        risk_level = SecuritySeverityEnum.CRITICAL if (has_critical and is_untrusted_source) else SecuritySeverityEnum.HIGH
        
        # Policy Enforcement: Untrusted source attempting override/exfil/action is strictly BLOCKED
        is_blocked = is_untrusted_source or has_critical
        recommended_action = "BLOCK" if is_blocked else "SANITIZE"

        logger.warning(
            f"PROMPT INJECTION GUARD: Detected {len(indicators)} indicators in source='{source}'. "
            f"Severity={risk_level.value}, Action={recommended_action}"
        )

        return {
            "detected": True,
            "risk_level": risk_level,
            "indicators": indicators,
            "sanitized_content": cls._sanitize_and_wrap(content, source, indicators),
            "recommended_action": recommended_action,
            "is_blocked": is_blocked
        }

    @classmethod
    def _check_obfuscated_payloads(cls, content: str, indicators: List[str]):
        """Checks for base64 encoded instruction blocks embedded in text."""
        b64_candidates = re.findall(r"\b[A-Za-z0-9+/]{24,}={0,2}\b", content)
        for cand in b64_candidates:
            try:
                decoded = base64.b64decode(cand).decode("utf-8", errors="ignore")
                for pattern in cls.OVERRIDE_PATTERNS + cls.EXFILTRATION_PATTERNS:
                    if re.search(pattern, decoded):
                        indicators.append(f"Obfuscated Base64 Prompt Injection Detected: '{pattern}'")
                        break
            except Exception:
                continue

    @classmethod
    def _wrap_as_inert_data(cls, content: str, source: str) -> str:
        """Wraps untrusted content in clear boundary tags so LLM treats it purely as passive data."""
        if source.upper() in cls.UNTRUSTED_SOURCES:
            return f"[UNTRUSTED_DATA_BOUNDARY source='{source}']\n{content}\n[/UNTRUSTED_DATA_BOUNDARY]"
        return content

    @classmethod
    def _sanitize_and_wrap(cls, content: str, source: str, indicators: List[str]) -> str:
        """Neutralizes detected instruction phrases and fences the remainder."""
        sanitized = content
        for pattern in cls.OVERRIDE_PATTERNS + cls.EXFILTRATION_PATTERNS + cls.DANGEROUS_ACTION_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED_SECURITY_POLICY_VIOLATION]", sanitized)
        return f"[UNTRUSTED_DATA_BOUNDARY source='{source}' security_alert='NEUTRALIZED_INJECTION']\n{sanitized}\n[/UNTRUSTED_DATA_BOUNDARY]"

prompt_guard = PromptInjectionGuard()
