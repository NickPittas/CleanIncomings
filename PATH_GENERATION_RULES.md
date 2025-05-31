# Path Generation Logic Clarifications for CleanIncomings App

This document outlines the rules for generating target folder paths based on filename patterns and user profiles.

## 1. Profile Structure (`profiles.json`)

-   Top-level keys are profile names (e.g., "Simple Project", "Sphere Project").
-   The value for each profile is an array of objects.
-   Each object in this array has a single key-value pair:
    -   **Key**: A relative path string (e.g., "3D\\Renders", "04_vfx"). This path is relative to the user-selected root output directory.
    -   **Value**: An array of strings (keywords from `patterns.json`, e.g., "beauty", "PREVIZ").

## 2. Matching Logic

### 2.1. Primary Keyword Driver
-   The **task** extracted from the filename is the primary driver for matching against the keyword lists in the profile.
-   If the extracted task is not present or does not lead to a match, the **asset** extracted from the filename will be used as a secondary driver.

### 2.2. Keyword Matching
-   A match occurs if *any single* keyword (task or asset, as per rule 2.1) extracted from the filename is present in a keyword list associated with a relative path in the selected profile.
-   Keyword matching (e.g., "beauty" from filename vs. "beauty" in `profiles.json`) should be **case-insensitive**.

### 2.3. Rule Specificity and Overlap
-   The order of path rules within a profile's array matters. The **first rule that matches** will be chosen.
-   There should ideally be no overlapping matches for a single extracted keyword across different path rules *under the same category* (e.g. a task keyword should not map to multiple categories).
-   If a keyword combination (e.g., a task like "beauty_gi") could ambiguously match multiple distinct primary keywords (e.g., "beauty" and "gi") that lead to different path rules, this should be flagged as "unmatched" in the UI, allowing the user to decide.

### 2.4. Handling No Match
-   If a file's extracted keywords (neither task nor asset) match any keyword lists in the selected profile, the file will be categorized as "footage" by default.
-   It will be placed in a default "footage" folder (the path for "footage" should be defined in the profile, e.g., "Videos\\Footage" for "Simple Project").
-   This default assignment must be flagged in the UI, allowing the user to review and modify it interactively.

## 3. Dynamic Path Segment Construction

### 3.1. Base Path
-   The relative path string chosen from `profiles.json` (e.g., "3D\\Renders") serves as the **base sub-path**.

### 3.2. Appending Dynamic Segments
-   Dynamic segments extracted from the filename are appended to this base sub-path.
-   **Shot Name**: Use as extracted (e.g., `WTFB0010` remains `WTFB0010`).
-   **Version Name**: Use as extracted (e.g., `v0055` remains `v0055`).

### 3.3. Order of Dynamic Segments
-   The fixed order for appending dynamic segments after the base sub-path is:
    1.  `SHOT`
    2.  `VERSION`
-   If a segment is not extracted from the filename (e.g., no resolution found), that part of the path is simply omitted. The original filename is then placed in the fully constructed directory.

### 3.4. Example
-   **Filename**: `WTFB0010_REND_FishFlock-2_v0055_.VrayRAW_.1001.exr`
-   **Extracted**: `shot="WTFB0010"`, `task="REND"`, `asset="VrayRAW"`, `version="v0055"`
-   **User Selected Root**: `D:\\New_folder`
-   **Profile Rule Match**: `task="REND"` matches a rule in the selected profile, which points to the base sub-path `"3D\\Renders"`. (The keywords `task="REND"` and `asset="VrayRAW"` are used for this lookup, not typically for creating additional path segments unless explicitly part of the profile's defined relative path string).
-   **Resulting Path**: `D:\\New_folder\\3D\\Renders\\WTFB0010\\v0055\\WTFB0010_REND_FishFlock-2_v0055_.VrayRAW_.1001.exr`
    (This assumes `SHOT` (`WTFB0010`) and `VERSION` (`v0055`) are appended to the base sub-path `3D\\Renders`. The original filename is then placed in this directory.)

## 4. Case Sensitivity for Generated Path Segments

-   Keyword matching against `profiles.json` lists is **case-insensitive**.
-   For the dynamic path segments (`SHOT`, `STAGE`, `TASK`, `ASSET`, `RESOLUTION`, `VERSION`) that form folder names:
    -   Their values are extracted from filenames.
    -   Case conversion rules are applied as follows:
        -   **Shot Name**: Preserved as-is from the filename (e.g., `OLNT0010` remains `OLNT0010`)
        -   **Resolution**: Converted to uppercase (e.g., `4k` becomes `4K`, `12k` becomes `12K`)
        -   **All others** (Stage, Task, Asset, Version): Converted to lowercase (e.g., `PREVIZ` becomes `previz`, `REND` becomes `rend`)

## 5. Final Path Assembly
-   The final path is constructed as:
    `USER_SELECTED_ROOT_DIR / [Base Sub-Path from Profile] / [Ordered Dynamic Segments with Case Rules Applied] / ORIGINAL_FILENAME`
