import re
from typing import Dict, Any

class SecretMasker:
    """
    Sanitizes secrets, tokens, API keys, and credentials from arguments, errors, and logs.
    """
    SECRET_PATTERNS = [
        re.compile(r'(ghp_[a-zA-Z0-9]{36,255})', re.IGNORECASE),
        re.compile(r'(github_pat_[a-zA-Z0-9_]{36,255})', re.IGNORECASE),
        re.compile(r'((?:bearer|token|password|secret|key)[\s:=]+)([^\s,;]+)', re.IGNORECASE)
    ]
    
    @classmethod
    def mask_text(cls, text: str) -> str:
        if not text:
            return ""
        masked = text
        # 1. Direct GitHub Token replacements
        masked = re.sub(r'ghp_[a-zA-Z0-9]{30,255}', '[MASKED_SECRET]', masked, flags=re.IGNORECASE)
        masked = re.sub(r'github_pat_[a-zA-Z0-9_]{30,255}', '[MASKED_SECRET]', masked, flags=re.IGNORECASE)
        # 2. Key-Value secrets
        masked = re.sub(r'((?:bearer|token|password|secret|key)[\s:=]+)([^\s,;]+)', r'\1[MASKED_SECRET]', masked, flags=re.IGNORECASE)
        return masked

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in data.items():
            if any(secret_key in k.lower() for secret_key in ["token", "password", "secret", "api_key", "auth"]):
                sanitized[k] = "[MASKED_SECRET]"
            elif isinstance(v, dict):
                sanitized[k] = cls.sanitize_dict(v)
            elif isinstance(v, str):
                sanitized[k] = cls.mask_text(v)
            else:
                sanitized[k] = v
        return sanitized
