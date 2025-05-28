import re
from typing import Optional, List

def extract_version_simple(filename: str, version_patterns: List[re.Pattern]) -> Optional[str]:
    for pattern in version_patterns:
        match = pattern.search(filename)
        if match:
            return match.group(0)
    return None
