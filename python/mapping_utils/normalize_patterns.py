import re
from typing import List

def normalize_regex_patterns(patterns: List[str]) -> List[str]:
    """
    Normalize regex patterns to ensure digit escapes (\\d) are present where expected.
    Fixes patterns like 'd{3,4}k' to '\\d{3,4}k' if missing.
    """
    normalized = []
    for pat in patterns:
        # Only fix if it looks like a digit quantifier and is not already escaped
        fixed = re.sub(r'(?<!\\)d(\{\d+,?\d*\})', r'\\d\1', pat)
        # Also fix d{...}x...d{...} (for res like 1920x1080)
        fixed = re.sub(r'(?<!\\)d(\{\d+,?\d*\})x(?<!\\)d(\{\d+,?\d*\})', r'\\d\1x\\d\2', fixed)
        normalized.append(fixed)
    return normalized
