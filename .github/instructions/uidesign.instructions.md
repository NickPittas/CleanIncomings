---
applyTo: '**'
---
# GitHub Copilot Instructions for Python Best Practices
## I. Core Principles for Code Quality & Design:

1. **Adhere to PEP 8 Strictly:**

Always follow Python Enhancement Proposal 8 (PEP 8) for code style. This includes naming conventions (e.g., snake_case for variables and functions, PascalCase for classes), indentation (4 spaces), line length (max 79 characters), and consistent spacing.

Prioritize readability through consistent formatting.

2. **Ensure Clarity and Readability:**

**Descriptive Naming:** 
Use clear, descriptive names for variables, functions, classes, and modules that accurately reflect their purpose. Avoid single-letter variables unless their context is immediately obvious (e.g., loop counters i, j).

**Meaningful Comments:** 
Add comments only when the code's intent is not immediately clear from its structure or naming. Explain why certain decisions were made, not what the code does (unless it's complex logic).

**Comprehensive Docstrings:**
Every module, class, method, and function must include a docstring explaining its purpose, arguments, return values, and any exceptions it might raise. Use reStructuredText or Google style docstrings for consistency.

3. **Apply the DRY (Don't Repeat Yourself) Principle:**

Identify and refactor redundant code blocks into reusable functions, classes, or modules.

Promote abstraction to avoid duplicating logic across different parts of the codebase.

4. **Promote Modularity and Maintainability:**

Single Responsibility Principle (SRP):
Each function, class, or module should have one, and only one, reason to change.

Small Functions:
Keep functions concise and focused on a single task. If a function becomes too long or complex, break it down into smaller, more manageable helper functions.

Loose Coupling, High Cohesion: 
Design components to be independent of each other (loose coupling) and ensure that elements within a component are functionally related (high cohesion).

Clear Interfaces:
Define clear and stable interfaces for classes and functions.

5. **Strive for Precision and Correctness:**

Explicit over Implicit:
Make intentions clear rather than relying on implicit behavior.

Error Handling:
Implement robust error handling using try-except blocks. Be specific with exception types.

Edge Cases:
Consider and handle common and unusual edge cases in logic.

## II. Agentic Mode Specific Directives:

1. **Codebase Contextual Awareness:**

Scan for Existing Solutions:
Before generating new code, actively scan the existing codebase for similar functionalities, utility functions, or classes that can be reused or extended.

Adhere to Project Patterns:
Understand and conform to the established architectural patterns, design choices, and conventions already present in the project.

Leverage Imports:
Suggest and utilize existing imports and modules within the project structure.

2. **Consistent Adherence to Rules:**

Self-Correction:
If a generated suggestion deviates from these guidelines, immediately self-correct and propose an alternative that aligns.

Prioritize Quality:
Always prioritize code quality, readability, and maintainability over mere functional completion.

## III. Development Workflow Integrations:

1. **Changelog Updates:**

When significant changes (new features, bug fixes, breaking changes) are introduced, prompt for or automatically suggest an update to the CHANGELOG.md file (or equivalent project-specific changelog).

Include a concise description of the change, its impact, and the relevant version number.

2. **Task Creation (TODO/FIXME):**

For incomplete features, known bugs, or areas requiring future attention, insert TODO: or FIXME: comments with a brief explanation and, if possible, a suggested next step.

Example: # TODO: Implement user authentication and authorization logic.

3. **Unit Testing:**

Encourage Test-Driven Development (TDD): 
When creating new features or fixing bugs, first suggest writing a failing unit test that describes the desired behavior.

Generate Tests: 
For new functions or classes, always suggest generating corresponding unit tests using standard Python testing frameworks (e.g., unittest or pytest).

Test Coverage: 
Aim for high test coverage, ensuring that critical paths and edge cases are tested.