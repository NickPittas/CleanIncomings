# Pattern Management Documentation

## Overview

This document describes the pattern management system implemented in the CleanIncomings application. Following requirements in `IMPORTANT.md` and `apprules.md`, all patterns are now exclusively loaded from `patterns.json`, with no hardcoded patterns anywhere in the codebase.

## Architectural Principles

1. **Single Source of Truth**: All patterns are stored and loaded from `patterns.json`
2. **No Path-based Searches**: All extraction functions use only filenames (never paths)
3. **Performance Optimization**: Pattern loading utilizes caching to minimize IPC calls
4. **Type Safety**: TypeScript interfaces define all pattern structures
5. **Centralization**: Pattern loading logic is isolated to dedicated modules

## Pattern Structure

The `patterns.json` file contains the following structure:

```json
{
  "shotPatterns": ["shot_(\\d{3})", "sh(\\d{3})"],
  "taskPatterns": {
    "comp": ["comp", "composite", "final"],
    "render": ["render", "beauty", "rgb"],
    "plate": ["plate", "bg", "background"]
  },
  "resolutionPatterns": ["(\\d{1,2}k)", "(\\d{3,4}x\\d{3,4})"],
  "versionPatterns": ["v(\\d{3})"],
  "assetPatterns": ["asset1", "asset2"],
  "stagePatterns": ["stage1", "stage2"]
}
```

## System Components

### 1. Backend (Python)

#### Pattern Loading

The `init_patterns_from_profile.py` function initializes patterns from `patterns.json`:

```python
def init_patterns_from_profile(mapping_generator, profile):
    """
    Initialize pattern-related properties from patterns.json only.
    
    Args:
        mapping_generator: The MappingGenerator instance
        profile: User profile data
    """
    # Load patterns only from patterns.json
    # No patterns are loaded from the profile to comply with IMPORTANT.md
    
    mapping_generator.shot_patterns = [re.compile(p) for p in mapping_generator.config.get('shotPatterns', [])]
    mapping_generator.task_patterns = mapping_generator.config.get('taskPatterns', {})
    mapping_generator.resolution_patterns = mapping_generator.config.get('resolutionPatterns', [])
    mapping_generator.version_patterns = [re.compile(p) for p in mapping_generator.config.get('versionPatterns', [])]
```

#### Extraction Functions

All extraction functions follow the same principle of using only the filename:

```python
def extract_shot_simple(filename: str, source_path: str, shot_patterns: List[re.Pattern]) -> Optional[str]:
    """
    Extract shot name from a filename using regex patterns.
    
    IMPORTANT: As per IMPORTANT.md, only the filename is used for extraction.
    Path components are completely ignored.
    
    Args:
        filename: The filename (without path) to extract from
        source_path: Source path (IGNORED - only for backward compatibility)
        shot_patterns: List of compiled regex patterns for shot extraction
    
    Returns:
        Extracted shot name or None if no match
    """
    # Search only in the filename, not in the path
    for pattern in shot_patterns:
        match = pattern.search(filename)
        if match:
            print(f"[SHOT_EXTRACTOR MATCH] Pattern: {pattern.pattern}, File: {filename}, Match: {match.group(0)}")
            return match.group(0)
    
    print(f"[SHOT_EXTRACTOR UNMATCHED] File: {filename}")
    return None
```

### 2. Frontend (TypeScript)

#### IPC Communication

The `patternHandlers.ts` file defines the IPC handlers for pattern loading:

```typescript
export const registerPatternHandlers = (ipcMain: IpcMain, config: any) => {
  // Handle request for all patterns
  ipcMain.handle('getPatterns', async () => {
    try {
      // Return all patterns from patterns.json
      return {
        shotPatterns: config.shotPatterns || [],
        taskPatterns: config.taskPatterns || {},
        resolutionPatterns: config.resolutionPatterns || [],
        versionPatterns: config.versionPatterns || [],
        assetPatterns: config.assetPatterns || [],
        stagePatterns: config.stagePatterns || []
      };
    } catch (error) {
      console.error('Error loading patterns:', error);
      throw error;
    }
  });

  // Handle request for profile-specific patterns
  ipcMain.handle('getProfilePatterns', async (_, profileId?: string) => {
    try {
      // Always return patterns from patterns.json, ignoring profile
      return {
        shotPatterns: config.shotPatterns || [],
        taskMaps: Object.entries(config.taskPatterns || {}).map(([task, aliases], index) => ({
          regex: `(?i)(${aliases.join('|')})`,
          canonical: task,
          priority: 100 - index
        })),
        resolutionPatterns: config.resolutionPatterns || [],
        versionPattern: config.versionPatterns?.[0] || ''
      };
    } catch (error) {
      console.error('Error loading profile patterns:', error);
      throw error;
    }
  });
};
```

#### Pattern Caching

The `patternCache.ts` utility provides caching for pattern loading:

```typescript
export const getPatternsCached = async (): Promise<{
  shotPatterns: string[];
  taskPatterns: Record<string, string[]>;
  resolutionPatterns: string[];
  versionPatterns: string[];
  assetPatterns: string[];
  stagePatterns: string[];
}> => {
  // If cache is valid, return from cache
  if (isCacheValid() && 
      cache.shotPatterns && 
      cache.taskPatterns && 
      cache.resolutionPatterns && 
      cache.versionPatterns) {
    console.log('Using cached patterns');
    return {
      shotPatterns: cache.shotPatterns,
      taskPatterns: cache.taskPatterns,
      resolutionPatterns: cache.resolutionPatterns,
      versionPatterns: cache.versionPatterns,
      assetPatterns: cache.assetPatterns || [],
      stagePatterns: cache.stagePatterns || []
    };
  }

  // Otherwise, fetch patterns from backend
  console.log('Fetching fresh patterns from backend');
  try {
    const patterns = await window.electronAPI.getPatterns();
    
    // Update cache
    cache.shotPatterns = patterns.shotPatterns;
    cache.taskPatterns = patterns.taskPatterns;
    cache.resolutionPatterns = patterns.resolutionPatterns;
    cache.versionPatterns = patterns.versionPatterns;
    cache.assetPatterns = patterns.assetPatterns || [];
    cache.stagePatterns = patterns.stagePatterns || [];
    cache.lastUpdated = Date.now();
    
    return patterns;
  } catch (error) {
    console.error('Error fetching patterns:', error);
    throw new Error('Failed to load patterns from backend');
  }
};
```

#### UI Integration

Components use the pattern cache to load patterns:

```typescript
useEffect(() => {
  // Load patterns using the caching system
  updateSettingsWithCachedPatterns({
    setShotNames,
    setResolutions,
    setTasks: setCustomTasks
  });
}, []);
```

## Testing the Pattern System

To ensure compliance with the requirements, run the unit tests:

```bash
cd python
python -m unittest tests/test_pattern_compliance.py
python -m unittest tests/test_integration.py
```

These tests verify:

1. All extraction functions only use filenames, not paths
2. All extraction functions fail gracefully when patterns are missing
3. All patterns are loaded from patterns.json, not hardcoded

## Modifying Patterns

To add or update patterns:

1. Edit the `patterns.json` file directly
2. For shot patterns: Add regex patterns to the `shotPatterns` array
3. For task patterns: Add task names as keys and their aliases as arrays in `taskPatterns`
4. For resolution patterns: Add regex patterns to the `resolutionPatterns` array
5. For version patterns: Add regex patterns to the `versionPatterns` array

## Best Practices

1. Always use only filename-based extraction
2. Never add hardcoded patterns to any part of the codebase
3. Update patterns.json when adding new pattern types
4. Use the caching system for UI components to improve performance
5. Invalidate the cache when patterns are updated

## Troubleshooting

If pattern extraction fails:

1. Check the log for `[*_EXTRACTOR UNMATCHED]` messages
2. Verify that patterns in patterns.json match your filenames
3. Ensure regex patterns are correctly formatted
4. Run the tests to verify pattern loading compliance

## Future Improvements

1. Add pattern validation to ensure valid regex patterns
2. Implement a UI for editing patterns.json directly
3. Add pattern testing tools to the UI
4. Enhance caching with local storage for faster startup
