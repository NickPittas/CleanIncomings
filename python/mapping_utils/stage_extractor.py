import re
from typing import Optional, List

def extract_stage_simple(filename: str, stage_patterns: list) -> Optional[str]:
    for stage in stage_patterns:
        if re.search(
            rf"(?<![a-zA-Z0-9]){re.escape(stage)}(?![a-zA-Z0-9])",
            filename,
            re.IGNORECASE,
        ):
            return stage
    return "unmatched"
