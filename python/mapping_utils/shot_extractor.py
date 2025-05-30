import re
import sys
from typing import Optional, List

def extract_shot_simple(filename: str, source_path: str, shot_patterns: List[str]) -> Optional[str]:
    """
    Extract shot information from a filename using patterns from patterns.json.
    It attempts to treat each pattern as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename, never the path.

    Args:
        filename: The filename to extract shot information from.
        source_path: Not used, kept for backward compatibility.
        shot_patterns: List of shot pattern strings from patterns.json.

    Returns:
        The matched shot pattern string if found, otherwise None.
    """
    if not shot_patterns:
        # print(f"[SHOT_EXTRACTOR DEBUG] No shot patterns provided for file '{filename}'.", file=sys.stderr, flush=True)
        return None

    # print(f"[SHOT_EXTRACTOR DEBUG] Attempting to extract shot from '{filename}' using patterns: {shot_patterns}", file=sys.stderr, flush=True)

    for pattern_str in shot_patterns:
        # print(f"[SHOT_EXTRACTOR DEBUG] Trying pattern (regex attempt): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
        try:
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
            match = compiled_pattern.search(filename)
            if match:
                matched_value = match.group(0) # Actual matched substring
                # print(f"[SHOT_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Matched: '{matched_value}'", file=sys.stderr, flush=True)
                return matched_value # Return the actual matched substring
            # else:
            #     print(f"[SHOT_EXTRACTOR DEBUG] Regex Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
        except re.error:
            # print(f"[SHOT_EXTRACTOR INFO] Pattern '{pattern_str}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
            # print(f"[SHOT_EXTRACTOR DEBUG] Trying pattern (simple string): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
            if pattern_str.lower() in filename.lower():
                # print(f"[SHOT_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}'", file=sys.stderr, flush=True)
                return pattern_str # Return the original pattern string
            # else:
            # print(f"[SHOT_EXTRACTOR DEBUG] Simple String Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)

    # print(f"[SHOT_EXTRACTOR DEBUG] No shot pattern matched for file '{filename}'.", file=sys.stderr, flush=True)
    return None
