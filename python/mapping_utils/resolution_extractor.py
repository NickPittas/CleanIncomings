import re
from typing import Optional, List

def extract_resolution_simple(filename: str, source_path: str, resolution_patterns: List[str]) -> Optional[str]:
    for pattern in resolution_patterns:
        if re.search(pattern, filename, re.IGNORECASE) or re.search(pattern, source_path, re.IGNORECASE):
            return pattern
    return None
