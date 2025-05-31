# AI Coding Assistant Configuration

## AI Coding Assistant Best Practices & Rules

### File Structure & Size

* **Max 500 lines per file**: split code into modules if exceeding.
* **One class/module per file**: maintain < 100 lines per class.
* Use descriptive filenames reflecting module purpose (`scan.py`, `ui_components.tsx`).

### Coding Standards

* **Python**: follow PEP8; use `black` for formatting; `flake8` for linting.
* **TypeScript/JavaScript**: follow Airbnb or standard style; enforce via ESLint/Prettier.
* **Type Safety**: use TypeScript interfaces/types for all React props and Electron IPC messages.

### Normalization Logic Rules

* Centralize regex patterns in config files (`shots.yaml`, `tasks.yaml`, `resolutions.yaml`).
* Sequence parsing function must have clear unit tests with edge cases.
* File-type rules prioritized by `priority` field; first-match applies.

### UI Development

* **Component Isolation**: each component should be < 300 lines.
* **Reusable Hooks**: extract common logic into custom React hooks (`useZustandStore`, `useIpcBridge`).
* **Accessibility**: all interactive elements must have ARIA labels.

### IPC & Data Flow

* Define JSON schemas for IPC messages; validate inbound messages.
* Keep Python CLI responses under 100 KB; paginate or stream if larger.

### Database & Persistence

* Use parameterized queries; avoid SQL injection.
* Wrap DB calls in transactions for batch operations.
* Migrate schemas with versioned SQL scripts; rollback on errors.

### Testing Guidelines

* **Unit Tests**: cover > 90% of core logic.
* **Property Tests**: use Hypothesis for Python normalization logic.
* **Component Tests**: mock IPC and DB; test UI state transitions.
* **E2E Tests**: simulate user drag-and-drop; verify FS changes in temp directories.
* Always run tests before CI merge; CI must block on test failures.

### Code Review & CI

* Require two approvals for PRs modifying core logic.
* CI pipeline stages:

  1. Lint (Python & JS)
  2. Unit Tests
  3. Integration Tests
  4. E2E Tests
  5. Package Build

### Copilot Movement Rules

* Copilot should stay within the file being edited unless cross-file references are updated.
* When updating a config value (e.g., a regex), Copilot moves to all usage sites for verification.
* For any new feature, Copilot should follow test-first approach: write tests before implementation.

---

## AI Coding Assistant Copilot Rules

1. **Context Awareness**

   * Copilot movements should prioritize related code blocks or sections when writing or updating normalization logic, UI components, or configuration definitions.
2. **Section-Based Editing**

   * When editing `README.md`, focus only within its boundaries; avoid touching `TASKS.md` or `Copilot_RULES.md`.
   * Similarly, editing `TASKS.md` or `Copilot_RULES.md` should not modify other files.
3. **Structured Updates**

   * For changes to mapping logic, locate `Normalization Logic & Data Models` section in `README.md` and `TASKS.md` accordingly.
   * When adjusting schema, Copilot should navigate to the `Database Schema` entries in `TASKS.md`.
4. **YAML/JSON Config Insertion**

   * When adding or updating `shot_codes`, `task_map`, or `res_patterns`, Copilot should target JSON/YAML code blocks under `Settings` or normalization sections.
5. **Testing Edits**

   * For test plan modifications, Copilot moves to the `Testing Strategy` in `README.md` and to `Unit`, `Integration`, `E2E` tasks in `TASKS.md`.
6. **Drag-and-Drop UI Rules**

   * Edits to UI workflows should occur in the `UI Components & Workflows` section of `README.md`.
7. **Profile Management Updates**

   * Profile CRUD or import/export changes should be edited in both `README.md` (Features & Getting Started) and `TASKS.md` (Week 7 tasks).

---

*End of configuration and rules files.*