import re
from typing import Optional, Dict, Any

def extract_task_simple(filename: str, source_path: str, task_patterns: Dict[str, Any]) -> Optional[str]:
    for task, patterns in task_patterns.items():
        for pattern in patterns:
            if re.search(pattern, filename, re.IGNORECASE) or re.search(pattern, source_path, re.IGNORECASE):
                return task
    return None
