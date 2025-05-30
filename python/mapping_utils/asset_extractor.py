import re
import sys
from typing import List, Optional

def extract_asset_simple(filename: str, asset_patterns: List[str]) -> Optional[str]:
    """
    Extract asset name from filename using patterns from patterns.json.
    It attempts to treat each pattern as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename, never the path.

    Args:
        filename: The filename to extract asset information from.
        asset_patterns: List of asset pattern strings from patterns.json.

    Returns:
        The matched asset pattern string if found, otherwise None.
    """
    if not asset_patterns:
        # print(f"[ASSET_EXTRACTOR DEBUG] No asset patterns provided for file '{filename}'.", file=sys.stderr, flush=True)
        return None

    # print(f"[ASSET_EXTRACTOR DEBUG] Attempting to extract asset from '{filename}' using patterns: {asset_patterns}", file=sys.stderr, flush=True)

    for pattern_str in asset_patterns:
        # print(f"[ASSET_EXTRACTOR DEBUG] Trying pattern (regex attempt): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
        try:
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
            match = compiled_pattern.search(filename)
            if match:
                matched_value = match.group(0)
                print(f"[ASSET_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Asset: '{pattern_str}', Matched: '{matched_value}'", file=sys.stderr, flush=True)
                return pattern_str # Return the original pattern string
            # else:
            #     print(f"[ASSET_EXTRACTOR DEBUG] Regex Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)
        except re.error:
            # print(f"[ASSET_EXTRACTOR INFO] Pattern '{pattern_str}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
            # print(f"[ASSET_EXTRACTOR DEBUG] Trying pattern (simple string): '{pattern_str}' on '{filename}'", file=sys.stderr, flush=True)
            if pattern_str.lower() in filename.lower():
                # print(f"[ASSET_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}', Asset: '{pattern_str}'", file=sys.stderr, flush=True)
                return pattern_str # Return the original pattern string
            # else:
            #     print(f"[ASSET_EXTRACTOR DEBUG] Simple String Pattern: '{pattern_str}' - NO MATCH on '{filename}'", file=sys.stderr, flush=True)

    # print(f"[ASSET_EXTRACTOR DEBUG] No asset pattern matched for file '{filename}'.", file=sys.stderr, flush=True)
    return None
