"""Shared detection patterns. Report pattern names and locations only; never echo matched values."""
import re

SECRET_PATTERNS = [
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("credentials in URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]{3,}@[^\s'\"]+", re.I)),
]

PLACEHOLDER = re.compile(r"(?i)(example|placeholder|changeme|dummy|xxxx|your[_-]|<[^>]+>|\$\{|\{\{)")

SENSITIVE_KEY = re.compile(
    r"(?i)(passw(?:or)?d|passwd|secret|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|"
    r"auth[_-]?token|access[_-]?token|refresh[_-]?token|bearer|authorization|cookie|session[_-]?id|otp|"
    r"\bpin\b|cvv|cvc|card[_-]?number|account[_-]?number|national[_-]?id|\bnik\b|\bktp\b|\bnpwp\b|\bssn\b|"
    r"passport|email|phone|msisdn|date[_-]?of[_-]?birth|\bdob\b)"
)

# Logger calls: logger.info(, log.warning(, logging.error(, self.logger.debug(, structlog/loguru style
LOG_CALL = re.compile(
    r"\b(?:[A-Za-z_][\w.]*\.)?(?:logger|log|logging|_logger|LOGGER|LOG)\."
    r"(?:debug|info|warning|warn|error|exception|critical|fatal|log)\s*\("
)

WHOLE_OBJECT = re.compile(
    r"(?i)\brequest\.(?:headers|body|data|POST|GET|json|META|cookies)\b|\bresponse\.(?:text|content|json\(\))|"
    r"\bvars\([^)]*\)|\.__dict__\b|\bheaders\b\s*[,)}]"
)


def find_secrets(text):
    """Yield (pattern_name, line_number) for high-confidence secret formats, skipping obvious placeholders."""
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in SECRET_PATTERNS:
            m = rx.search(line)
            if m and not PLACEHOLDER.search(m.group(0)):
                yield name, lineno
                break
