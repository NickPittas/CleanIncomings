import re
import sys
from typing import Optional, List

def extract_resolution_simple(filename: str, source_path: str, resolution_patterns: List[str]) -> Optional[str]:
    """
    Extract resolution information from a filename using patterns from patterns.json.
    It attempts to treat each pattern as a regular expression first (case-insensitive).
    If a pattern is not valid regex, it falls back to a simple case-insensitive string containment check.
    According to IMPORTANT.md guidelines, we ONLY search the filename, never the path.

    Args:
        filename: The filename to extract resolution information from.
        source_path: Not used, kept for backward compatibility.
        resolution_patterns: List of resolution pattern strings from patterns.json.
                           These can be simple strings (e.g., "2k") or regex patterns (e.g., "(?i)proxy").

    Returns:
        The matched resolution pattern string if found, otherwise None.
    """
    # IMPORTANT: Only search the filename, not the path
    for pattern_str in resolution_patterns:
        try:
            # Attempt to compile and match as regex, case-insensitive by default.
            # If pattern_str itself contains (?i), that will also ensure case-insensitivity.
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
            match = compiled_pattern.search(filename) # Search on original filename
            if match:
                print(f"[RESOLUTION_EXTRACTOR MATCH] Regex Pattern: '{pattern_str}', File: '{filename}', Matched Group: '{match.group(0)}'", file=sys.stderr, flush=True)
                return match.group(0) # Return the actual matched substring
            else:
                # This 'else' is for when regex compilation succeeded but no match was found.
                # We don't print an 'UNMATCHED' here for every non-matching regex, 
                # as a pattern might be intended for simple string match if it fails regex compilation.
                # However, if it compiled fine but didn't match, it just means this specific regex pattern didn't match.
                pass
        except re.error:
            # If re.compile fails, the pattern_str is not valid regex.
            # Fallback to simple string containment for this pattern.
            print(f"[RESOLUTION_EXTRACTOR INFO] Pattern '{pattern_str}' is not valid regex. Trying as simple string.", file=sys.stderr, flush=True)
            if pattern_str.lower() in filename.lower():
                print(f"[RESOLUTION_EXTRACTOR MATCH] Simple String: '{pattern_str}', File: '{filename}'", file=sys.stderr, flush=True)
                return pattern_str
            # else: # No explicit 'else' needed here for unmatched simple string, loop continues

    # If loop completes without returning, no pattern matched either way.
    print(f"[RESOLUTION_EXTRACTOR UNMATCHED] No pattern in {resolution_patterns} matched file '{filename}'", file=sys.stderr, flush=True)
    return None
