import re
from typing import Optional

import re
from typing import Optional, List

def extract_shot_simple(filename: str, source_path: str, shot_patterns: List[re.Pattern]) -> Optional[str]:
    for pattern in shot_patterns:
        match = pattern.search(filename) or pattern.search(source_path)
        if match:
            return match.group(0)
    return None
