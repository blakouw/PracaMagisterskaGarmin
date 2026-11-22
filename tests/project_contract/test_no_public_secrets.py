from __future__ import annotations

import re

from registry_helpers import ROOT, file_text, public_text_files


SECRET_PATTERNS = [
    ("private_pem_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")),
    ("openai_api_key_assignment", re.compile(r"OPENAI_API_KEY\s*=\s*['\"]?(sk-[A-Za-z0-9_-]{20,})")),
    ("bearer_token", re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{24,}", re.IGNORECASE)),
    ("garmin_token_assignment", re.compile(r"(?:GARMIN|garmin).{0,30}(?:TOKEN|token)\s*=\s*['\"]?[A-Za-z0-9._~+/=-]{24,}")),
    ("plain_password_assignment", re.compile(r"(?<!example_)(?:password|passwd)\s*=\s*['\"][^'\"\n]{12,}['\"]", re.IGNORECASE)),
]


def test_public_text_files_do_not_contain_probable_real_secrets() -> None:
    findings: list[tuple[str, str]] = []
    for path in public_text_files():
        text = file_text(path)
        for finding_type, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append((path.relative_to(ROOT).as_posix(), finding_type))
    assert findings == []


def test_secret_scanner_does_not_flag_documented_placeholder_names() -> None:
    safe_examples = [
        "OPENAI_API_KEY",
        "Authorization: Bearer <token>",
        "Do not commit real secrets.",
        "example_token.json",
    ]
    for example in safe_examples:
        for _, pattern in SECRET_PATTERNS:
            assert pattern.search(example) is None
