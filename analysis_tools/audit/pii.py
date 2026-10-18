# analysis_tools/audit/pii.py
"""PII pattern scan (gate G9). Empty list = clean."""
import re

_PATTERNS = [
    (re.compile(r"\b09\d{9}\b"), "phone"),
    (re.compile(r"\b\d{16}\b"), "card"),
    (re.compile(r"\bIR\d{24}\b"), "iban"),
    (re.compile(r"\b\d{10}\b"), "possible national id"),
]

def scan(text):
    return [f"{kind}: {m.group(0)}" for pat, kind in _PATTERNS
            for m in pat.finditer(text)]
