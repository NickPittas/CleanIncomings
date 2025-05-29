import re
import sys
from typing import Optional, Dict, Any, List

def extract_task_simple(filename: str, source_path: str, task_patterns: Dict[str, List[str]]) -> Optional[str]:
    """
    Extract task information from a filename using patterns from patterns.json.
    It attempts to treat each pattern in the lists as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename, never the path.

    Args:
        filename: The filename to extract task information from.
        source_path: Not used, kept for backward compatibility.
        task_patterns: Dictionary of task patterns (key=task name, value=list of pattern strings).

    Returns:
        The matched task name (key) if found, otherwise None.
    """
    if not task_patterns:
        print(f"[TASK_EXTRACTOR DEBUG] No task patterns provided for file '{filename}'.", file=sys.stderr, flush=True)
        return None

    print(f"[TASK_EXTRACTOR DEBUG] Attempting to extract task from '{filename}' using patterns: {task_patterns}", file=sys.stderr, flush=True)

    for task, pattern_list in task_patterns.items():
        print(f"[TASK_EXTRACTOR DEBUG] Checking patterns for task: '{task}' on file '{filename}'", file=sys.stderr, flush=True)
        for pattern_str in pattern_list:
            print(f"[TASK_EXTRACTOR DEBUG] Trying pattern (regex attempt): '{pattern_str}' for task '{task}' on '{filename}'", file=sys.stderr, flush=True)
            try:
                compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                match = compiled_pattern.search(filename)
                if match:
                    matched_value = match.group(0)
                    print(f"[TASK_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Task: '{task}', Matched: '{matched_value}'", file=sys.stderr, flush=True)
                    return task
                else:
                    print(f"[TASK_EXTRACTOR DEBUG] Regex Pattern: '{pattern_str}' for task '{task}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
            except re.error:
                print(f"[TASK_EXTRACTOR INFO] Pattern '{pattern_str}' for task '{task}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
                print(f"[TASK_EXTRACTOR DEBUG] Trying pattern (simple string): '{pattern_str}' for task '{task}' on '{filename}'", file=sys.stderr, flush=True)
                if pattern_str.lower() in filename.lower():
                    print(f"[TASK_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}', Task: '{task}'", file=sys.stderr, flush=True)
                    return task
                else:
                    print(f"[TASK_EXTRACTOR DEBUG] Simple String Pattern: '{pattern_str}' for task '{task}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
    
    print(f"[TASK_EXTRACTOR DEBUG] No task pattern matched for file '{filename}'.", file=sys.stderr, flush=True)
    return None
