# TASKS.md

## Mapping Refactor Preservation Steps
- [x] Identify all MappingGenerator methods previously internal (e.g. _group_image_sequences, _process_file_for_sequence, _create_sequence_mapping, _extract_sequence_info, _init_patterns_from_profile, etc.) that need modularization.
- [x] Ensure each such method is extracted to its own module in mapping_utils with matching function/class signatures and docstrings.
    - [x] _create_simple_mapping → mapping_utils/create_simple_mapping.py
    - [x] _generate_simple_target_path → mapping_utils/generate_simple_target_path.py
    - [x] _group_image_sequences → mapping_utils/group_image_sequences.py
    - [x] _process_file_for_sequence → mapping_utils/process_file_for_sequence.py
        - [x] Import process_file_for_sequence in mapping.py
        - [x] Audit and update all call sites for process_file_for_sequence
        - [x] No further usages or legacy references found in mapping.py
    - [x] _create_sequence_mapping → mapping_utils/create_sequence_mapping.py
        - [x] Extract logic to mapping_utils/create_sequence_mapping.py (already implemented and exposed)
        - [x] Import create_sequence_mapping in mapping.py (already present)
        - [ ] Audit and update all call sites for create_sequence_mapping (no usages in mapping.py; check tests/legacy files)
    - [ ] _create_sequence_mapping → mapping_utils/create_sequence_mapping.py
    - [ ] _extract_sequence_info → mapping_utils/extract_sequence_info.py
    - [ ] _init_patterns_from_profile → mapping_utils/init_patterns_from_profile.py
- [ ] Import each modularized function/class into mapping.py, replacing all previous internal usages with the new import.
    - [ ] Import and update all usages for group_image_sequences
    - [ ] Import and update all usages for process_file_for_sequence
    - [ ] Import and update all usages for create_sequence_mapping
    - [ ] Import and update all usages for extract_sequence_info
    - [ ] Import and update all usages for init_patterns_from_profile
- [ ] Update all references in MappingGenerator and related code to use the new modularized functions, ensuring argument and return value compatibility.
    - [ ] For each method above, audit all call sites and update arguments/returns as needed
- [ ] Verify that all logic, including edge cases and error handling, is preserved exactly as in the original mapping.py.bak.
- [ ] Run all existing unit, integration, and E2E tests to confirm no regressions or breakages.
- [ ] Compare the output and behavior of the refactored mapping.py with the original backup on representative data sets.
- [ ] Document all changes and the new modular structure in README and code comments.
- [ ] Perform a final review for completeness, maintainability, and adherence to project rules (file size, modularity, test-first, etc.).



## Open Tasks
- [ ] Add component tests (mock IPC/DB) for React UI
- [ ] Add E2E tests (drag-and-drop, FS changes)
- [ ] Implement CI pipeline (lint, test, build)
- [ ] Add schema migration scripts for SQLite DB
- [ ] Paginate/stream large Python responses
- [ ] Add ARIA/accessibility to all UI components
- [ ] Document test plans and profile CRUD in README/TASKS
- [ ] Revisit and implement backend progress reporting for file operations (move/copy) if needed, using a robust and maintainable approach (e.g., IPC, polling, or websocket).
- [ ] E2E test: Copy/move operation with real-time progress bar, filenames, and ETA updates
- [ ] Component test: Progress bar UI with mocked backend progress
- [ ] Backend: Implement and test progress reporting for file operations (move/copy) to support frontend progress bar
- [ ] Implement a test mode (simulation) for file operations, so that tests can run without touching the real filesystem
- [x] Backend: Fix NoneType arithmetic in fileops.py (copy/move logic)
- [x] Backend: Add unit tests for file/sequence copy/move, error cases
- [x] Backend: Add integration tests for apply_mappings and progress
- [ ] Frontend: Add integration test for copy/move operation (mock backend)
- [ ] Frontend: Validate error handling and user feedback for failed operations
- [ ] E2E: Simulate drag-and-drop and verify FS changes for copy/move
- [ ] Backend: Implement scan progress tracking and polling endpoint (scan_batch_id, progress file, get_scan_progress, include folders scanned and ETA)
- [ ] Frontend: Poll scan progress and update progress bar in real time (show folders scanned and ETA)
- [ ] Test: Integration test for scan progress reporting and UI update (including folders scanned and ETA)

## Completed Tasks
- [x] Split `python/normalizer.py` into modules (<500 lines each)
    - `scanner.py`, `mapping.py`, `fileops.py` now exist
    - All MappingGenerator logic is in `mapping.py`
- [x] Add unit tests for all normalization logic (Python)
    - Tests for shot, task, version, resolution extraction
    - All tests pass (see `python/test_mapping.py`)
- [x] Add property tests (Hypothesis) for normalization
    - Property-based tests for all normalization logic
    - All tests pass, logic robust to edge cases

## Testing Strategy
- Unit: pytest for all backend logic, 90%+ coverage
- Property: Hypothesis for normalization edge cases
- Component: React Testing Library, mock IPC/DB
- E2E: Simulate drag-and-drop, verify FS changes

## Database/Schema Checklist
- [ ] Versioned migration scripts
- [ ] Rollback on error

## Profile CRUD/Test Plan
- [ ] Profile create, update, import/export, test

## Accessibility/ARIA Checklist
- [ ] All interactive UI elements have ARIA labels

## CI Pipeline
1. Lint (Python & JS)
2. Unit Tests
3. Integration Tests
4. E2E Tests
5. Package Build

## Testing Strategy
- **Unit tests:** >90% coverage for core logic (Python, JS/TS)
- **Property tests:** Use Hypothesis for normalization logic
- **Component tests:** Mock IPC/DB, test UI state transitions
- **E2E tests:** Simulate user drag-and-drop, verify FS changes

## Database/Schema Migration Checklist
- [ ] All DB changes via versioned SQL scripts
- [ ] Rollback on migration errors
- [ ] Test migrations in CI

## Profile CRUD/Test Plan
- [ ] Unit tests for create/read/update/delete profiles
- [ ] Import/export profile tests
- [ ] UI tests for profile management

## Accessibility/ARIA Checklist
- [ ] All interactive elements have ARIA labels
- [ ] Keyboard navigation for all UI
- [ ] Screen reader support

## CI Pipeline Stages
1. Lint (Python & JS)
2. Unit Tests
3. Integration Tests
4. E2E Tests
5. Package Build

## Completed Tasks
- [x] Remove redundant test files
- [x] Enforce config-only normalization logic
- [x] TypeScript strictness in store
- [x] Conflict detection before file ops 