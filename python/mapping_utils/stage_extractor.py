import re
import sys
from typing import Optional, List

def extract_stage_simple(filename: str, stage_patterns: List[str]) -> Optional[str]:
    """
    Extract stage information from a filename using patterns from patterns.json.
    It attempts to treat each pattern as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename.

    Args:
        filename: The filename to extract stage information from.
        stage_patterns: List of stage pattern strings from patterns.json.

    Returns:
        The matched stage pattern string if found, otherwise None.
    """
    if not stage_patterns:
        # print(f"[STAGE_EXTRACTOR DEBUG] No stage patterns provided for file '{filename}'.", file=sys.stderr, flush=True)
        return None

    # print(f"[STAGE_EXTRACTOR DEBUG] Attempting to extract stage from '{filename}' using patterns: {stage_patterns}", file=sys.stderr, flush=True)

    for pattern_str in stage_patterns:
        # print(f"[STAGE_EXTRACTOR DEBUG] Trying pattern (regex attempt): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
        try:
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
            match = compiled_pattern.search(filename)
            if match:
                matched_value = match.group(0)
                # print(f"[STAGE_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Stage: '{pattern_str}', Matched: '{matched_value}'", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)
                return pattern_str # Return the original pattern string
            # else:
            #     print(f"[STAGE_EXTRACTOR DEBUG] Regex Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
        except re.error:
            # print(f"[STAGE_EXTRACTOR INFO] Pattern '{pattern_str}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
            # print(f"[STAGE_EXTRACTOR DEBUG] Trying pattern (simple string): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
            if pattern_str.lower() in filename.lower():
                # print(f"[STAGE_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}', Stage: '{pattern_str}'", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)
                return pattern_str # Return the original pattern string
            # else:
            #     print(f"[STAGE_EXTRACTOR DEBUG] Simple String Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)

    # print(f"[STAGE_EXTRACTOR DEBUG] No stage pattern matched for file '{filename}'.", file=sys.stderr, flush=True)
    return None
