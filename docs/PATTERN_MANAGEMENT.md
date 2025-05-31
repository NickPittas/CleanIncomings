# Pattern Management Documentation

## Overview

This document details the pattern management system within the CleanIncomings application. In strict adherence to the guidelines outlined in `IMPORTANT.md` and the project's coding standards (`.github/copilot-instructions.md`), all filename parsing patterns are exclusively defined and loaded from the `config/patterns.json` file. This ensures a centralized, data-driven approach to filename normalization, eliminating hardcoded patterns from the Python backend and TypeScript frontend codebase.

## Architectural Principles

1. **Single Source of Truth**: `config/patterns.json` is the sole repository for all regular expressions and keyword lists used for extracting information (shot, task, version, etc.) from filenames.
2. **Filename-Only Parsing**: All extraction logic operates *solely* on the filename string. File paths are not used for pattern matching to ensure consistency regardless of the file's location.
3. **Dynamic Loading & Caching**: Patterns are loaded dynamically at runtime. The frontend may employ caching mechanisms to minimize redundant IPC calls for pattern retrieval.
4. **Type Safety (Frontend)**: TypeScript interfaces should be used to define the structure of pattern objects received from the backend, ensuring type safety in UI components that might interact with or display pattern information.
5. **Centralized Logic**: Pattern loading and parsing logic are encapsulated within dedicated modules/functions in both the backend (Python) and frontend (TypeScript) to promote separation of concerns.

## `patterns.json` Structure

The `config/patterns.json` file typically holds key-value pairs where keys represent pattern categories (e.g., `versionPatterns`, `shotPatterns`, `taskPatterns`) and values are arrays of strings (regex patterns or keywords).

**Example `config/patterns.json`:**
```json
{
  "comment": "Patterns for filename normalization. All regex should be JSON-escaped.",
  "versionPatterns": [
    "_v(\\d+)",
    "\\.v(\\d+)",
    "ver(\\d+)"
  ],
  "shotPatterns": [
    "([A-Z]{2,4}\\d{3,4})",
    "(sh\\d{4})"
  ],
  "taskPatterns": {
    "REND": ["render", "rend", "beauty"],
    "COMP": ["comp", "composite", "final"],
    "PLATE": ["plate", "bg", "background"],
    "PREVIZ": ["previz", "animatic"]
  },
  "assetPatterns": [
    "assetName_([a-zA-Z0-9_]+)"
  ],
  "resolutionPatterns": [
    "(\\d{3,4}x\\d{3,4})"
  ],
  "framePatterns": [
    "(\\d{4,8})\\.exr",
    "\\.(\\d{1,8})\\."
  ]
}
```
- **`taskPatterns`**: This is an object where keys are the canonical task names (e.g., "REND") and values are arrays of aliases or keywords that map to that canonical task. During parsing, if a filename keyword matches an alias (e.g., "beauty"), it's normalized to the canonical task name ("REND").
- Other `*Patterns` are typically arrays of regex strings. These regex patterns should be crafted to include capturing groups for the specific information to be extracted (e.g., `_v(\\d+)` captures the version number).

## System Components

### 1. Backend (Python - e.g., in `python/core/normalizer.py` or similar)

#### Pattern Loading:
- Patterns are loaded from `config/patterns.json` when the normalization service or relevant component is initialized.
- Regular expressions are compiled using `re.compile()` for performance.

```python
# Example snippet from a hypothetical Normalizer class
import json
import re

class Normalizer:
    def __init__(self, patterns_file_path="config/patterns.json"):
        self.patterns = self._load_patterns(patterns_file_path)
        self.compiled_patterns = self._compile_patterns()

    def _load_patterns(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def _compile_patterns(self):
        compiled = {}
        if "versionPatterns" in self.patterns:
            compiled["version"] = [re.compile(p, re.IGNORECASE) for p in self.patterns["versionPatterns"]]
        if "shotPatterns" in self.patterns:
            compiled["shot"] = [re.compile(p, re.IGNORECASE) for p in self.patterns["shotPatterns"]]
        if "taskPatterns" in self.patterns:
            compiled["task"] = {}
            for canonical_task, aliases in self.patterns["taskPatterns"].items():
                for alias in aliases:
                    compiled["task"][re.compile(alias, re.IGNORECASE)] = canonical_task
        return compiled

    def extract_version(self, filename):
        if "version" in self.compiled_patterns:
            for pattern in self.compiled_patterns["version"]:
                match = pattern.search(filename)
                if match and match.groups():
                    return match.group(1)
        return None
    
    def extract_task(self, filename):
        if "task" in self.compiled_patterns:
            for pattern_regex, canonical_task in self.compiled_patterns["task"].items():
                if pattern_regex.search(filename):
                    return canonical_task
        return None
```

#### Extraction Functions:
- Each extraction function (e.g., `extract_shot`, `extract_task`, `extract_version`) takes only the `filename` string as input.
- It iterates through the relevant compiled patterns for its category.
- The first successful match is typically returned. For regex with capturing groups, the content of the group is returned.
- Matching is generally case-insensitive (`re.IGNORECASE`).

### 2. Frontend (TypeScript - e.g., in Electron main process or preload script)

#### IPC Communication for Patterns:
- If the UI needs to display or manage patterns, IPC handlers can be set up.

#### Pattern Caching:
- If patterns are frequently requested by the UI, a simple caching mechanism in the renderer process or preload script can improve responsiveness.

## Testing the Pattern System

Comprehensive unit tests are crucial to ensure the pattern system works as expected and adheres to project rules.

**Example Test Cases (Python `unittest`):**
- Verify that all extraction functions use only filenames.
- Test that extraction functions correctly parse filenames based on `patterns.json` content.
- Test edge cases: filenames with multiple potential matches, filenames with no relevant patterns.
- Test case-insensitivity.
- Test handling of missing pattern categories in `patterns.json`.

```bash
# Example command to run tests
cd python
python -m unittest discover tests -p "test_normalizer.py"
python -m unittest discover tests -p "test_pattern_integration.py"
```

## Modifying Patterns

To add, remove, or update filename parsing patterns:

1. **Directly edit `config/patterns.json`**. This is the *only* place patterns should be changed.
2. For patterns requiring regular expressions: Add or modify the regex strings in the respective arrays.
3. For `taskPatterns`: Modify the object by adding new canonical task keys or updating the alias arrays for existing tasks.
4. After modifying `patterns.json`, restart the application to ensure the changes are loaded.
5. Add new unit tests for any new or significantly modified patterns to verify their correctness.

## Best Practices

1. **Strictly Adhere to Filename-Only Parsing**: Never allow path components to influence pattern matching.
2. **Maintain `patterns.json` as the Single Source**: Avoid any temptation to hardcode patterns or pattern-like logic elsewhere.
3. **Prioritize Clear and Efficient Regex**: Strive for clarity and efficiency. Add comments in `patterns.json` if a regex is particularly complex.
4. **Validate `patterns.json` Structure**: Consider adding a validation step on application startup to check if `patterns.json` conforms to the expected schema.
5. **Version Control for `patterns.json`**: Ensure it's tracked in version control.

## Troubleshooting Pattern Issues

If filename normalization is not working as expected:
1. **Check Application Logs**: Look for messages like `[*_EXTRACTOR UNMATCHED]`.
2. **Verify `config/patterns.json`**: Ensure the JSON syntax is valid and regex patterns are correct.
3. **Test Regex Patterns**: Use an online regex tester or Python's `re` module interactively to test your patterns.
4. **Examine Extracted Data**: Log the data extracted by each pattern to see what the system is identifying.
