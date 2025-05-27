# VFX Folder Normalizer

A cross-platform Electron + Python app for robust, configurable VFX project folder normalization.

## Features
- Fast, deep folder scanning (network-friendly)
- Config-driven normalization logic (edit patterns in the UI)
- Real file move/copy with conflict detection (accept/deny/replace)
- Progress tracking (with ETA, cancel, pause/resume)
- SQLite operation tracking and undo
- Modular, testable backend (Python)
- Modern, accessible React UI (TypeScript)

## Quickstart
1. **Install dependencies:**
   ```sh
   yarn install
   pip install -r python/requirements.txt
   ```
2. **Start the app:**
   ```sh
   yarn dev
   # or use the provided start-dev.bat
   ```
3. **Scan a folder, select a profile, and normalize!**

## Testing
- **Python:**
  - Run all unit/property tests:
    ```sh
    pytest
    ```
- **JS/TS:**
  - Run all component/unit tests:
    ```sh
    yarn test
    ```

## Updating Normalization Patterns
- Edit via the app UI (Settings > Patterns), or directly in `src/config/patterns.json`.
- All regex and mapping logic is config-driven.

## Coding & CI Rules
- Max 500 lines per file, 1 class/module per file (<100 lines/class)
- Python: PEP8, black, flake8; JS/TS: Airbnb/standard, ESLint/Prettier
- All normalization logic must be unit/property tested (>90% coverage)
- CI blocks on lint/test failures
- See `TASKS.md` for detailed dev workflow

## Contributing
- Fork, branch, and submit PRs (2 approvals for core logic)
- Add/maintain tests for all new features
- See `TASKS.md` for open tasks and roadmap 