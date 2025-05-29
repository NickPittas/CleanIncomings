# IMPORTANT: Mapping and Normalization Refactor Guidance

## Tasks & Guidance

1. **Filename-Only Search**
   - All pattern searches (shot, task, resolution, version, project type, asset, stage) must be performed on the filename only, never on the path.

2. **Centralized Patterns**
   - All search patterns must come from `patterns.json`. No hardcoded patterns or logic for shot, task, resolution, version, project type, asset, or stage should exist in the codebase.

3. **Pattern Usage**
   - For each mapping type (shot, task, resolution, version, project type, asset, stage), only use the patterns defined in `patterns.json`.
   - The only pattern that may use a regex is the version number, but the system should support regex for any pattern if defined as such in `patterns.json`.
   - All other patterns should be matched exactly as they appear (case-insensitive substring match, unless otherwise specified in `patterns.json`).

4. **Frontend & Backend Refactor**
   - Remove all hardcoded patterns and mapping logic from both the frontend and backend.
   - Ensure the UI settings dynamically read and use `patterns.json` for all mapping and normalization.
   - All normalization and mapping logic must use only the patterns from `patterns.json`.

5. **Profiles Refactor**
   - Move all profile definitions to a `Profiles.json` or `Profiles.yaml` file.
   - Profiles should only define:
     - The base/root path for the project.
     - The folder structure for each asset type (e.g., where to place shots, renders, plates, videos, etc.).
   - No pattern or mapping logic should remain in the profile definition—just folder structure and root path.

6. **Mapping Flow**
   - For each file, search the filename with each pattern in the relevant category from `patterns.json`.
   - When a pattern is found, record the exact match (case-insensitive) for use in path construction and memory.
   - Continue this process for all mapping categories.

7. **Memory and Path Construction**
   - Use the exact matched value from the filename (not the pattern itself) for path construction and memory.

8. **Strict Pattern Source**
   - Never use any pattern or mapping logic that is not defined in `patterns.json`.
   - All mapping and normalization must be fully data-driven from `patterns.json`.

9. **Testing & Validation**
   - Add tests to verify that all mapping logic fails if a required pattern is missing from `patterns.json`.
   - Add tests to ensure no hardcoded patterns or logic remain in the codebase.

---

> **This document is the main guide for all mapping and normalization logic. All contributors must follow these rules strictly.**
