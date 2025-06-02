import re
import sys
from typing import Optional, List

def extract_version_simple(filename: str, version_patterns: List[str]) -> Optional[str]:
    """
    Extract version information from a filename using patterns from patterns.json.
    It attempts to treat each pattern as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename.

    Args:
        filename: The filename to extract version information from.
        version_patterns: List of version pattern strings from patterns.json.

    Returns:
        The matched version pattern string if found, otherwise None.
    """
    if not version_patterns:
        # print(f"[VERSION_EXTRACTOR DEBUG] No version patterns provided for file '{filename}'.", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)
        return None

    # print(f"[VERSION_EXTRACTOR DEBUG] Attempting to extract version from '{filename}' using patterns: {version_patterns}", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)

    for pattern_str in version_patterns:
        # print(f"[VERSION_EXTRACTOR DEBUG] Trying pattern (regex attempt): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
        try:
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
            match = compiled_pattern.search(filename)
            if match:
                matched_value = match.group(0)
                # print(f"[VERSION_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Matched: '{matched_value}'", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)
                return matched_value # Return the actual matched string
            # else:
            #     print(f"[VERSION_EXTRACTOR DEBUG] Regex Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
        except re.error:
            # print(f"[VERSION_EXTRACTOR INFO] Pattern '{pattern_str}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
            # print(f"[VERSION_EXTRACTOR DEBUG] Trying pattern (simple string): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
            if pattern_str.lower() in filename.lower():
                # print(f"[VERSION_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}'", file=sys.stderr, flush=True)  # (Silenced for normal use. Re-enable for troubleshooting.)
                return pattern_str # Return the original pattern string
            # else:
            #     print(f"[VERSION_EXTRACTOR DEBUG] Simple String Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)

    # print(f"[VERSION_EXTRACTOR DEBUG] No version pattern matched for file '{filename}'.", file=sys.stderr, flush=True)
    return None
