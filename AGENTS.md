# Agent Guidelines for dash-router

This repository contains a Python library for file-system routing in Flash/Quart.
Use this document to stay aligned with existing patterns and workflows.

## Repository Basics
- Language: Python 3.12+
- Packaging: Poetry (pyproject.toml)
- Primary module: `flash_router`

## Build / Lint / Test

### Install
- `poetry install`

### Build
- `poetry build`

### Lint
- No lint tool is configured in the repo.
- If you add linting locally, prefer `ruff` and `black` and keep changes minimal.

### Tests
- There is no test runner configured.
- The only test-like file is `test.py` (a minimal usage example).
- Basic run: `poetry run python test.py`
- Test app: `poetry run python tests/test_app.py`
  - Dumps route table/tree JSON to `tests/utils/route_table.json` and
    `tests/utils/route_tree.json`.

### Single Test
- No single-test workflow exists yet.
- If you introduce pytest later, use:
  - `poetry run pytest path/to/test_file.py::TestClass::test_name`
  - `poetry run pytest -k test_name`

## Cursor / Copilot Rules
- No Cursor rules found in `.cursor/rules/` or `.cursorrules`.
- No GitHub Copilot rules found in `.github/copilot-instructions.md`.

## Code Style Guidelines

### Imports
- Follow this order: standard library, third-party, then local imports.
- Keep related imports grouped (see `flash_router/router.py`).
- Use explicit imports from `typing` instead of `typing.*`.

### Formatting
- 4-space indentation.
- Keep line length reasonable and avoid extremely long lines.
- Use blank lines to separate logical sections and class definitions.
- Prefer trailing commas in multi-line collections for cleaner diffs.

### Typing
- Use modern Python typing: `str | None` instead of `Optional[str]`.
- Use `Dict`, `List`, and `Callable` from `typing` where needed.
- For public APIs, annotate inputs and return values.
- Pydantic models are used for config objects (see `RouteConfig`).

### Naming Conventions
- Classes: `PascalCase` (e.g., `RouteTree`, `ExecNode`).
- Functions and variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE` (see `DEFAULT_LAYOUT_TOKEN`).
- Route-related files:
  - `page.py` contains `layout` and optional `config`.
  - `api.py` contains `endpoint`.
  - `loading.py` and `error.py` expose `layout`.

### File/Folder Conventions
- Route folders map to URL segments.
- Slots are folders with names like `(slot_name)`.
- Path templates use `[param]` folder names.
- Catch-all uses `[__rest]`.

### Layout Functions
- A `layout` can be a component or a callable that returns one.
- Layouts can be async for Flash/Quart.
- Layouts and endpoints accept keyword args extracted from URL/query params.
- Keep layout functions side-effect free; data comes from `endpoint`.

### Error Handling
- The router prefers explicit exceptions with clear messages.
- Errors in layout or endpoint execution should be handled via `error.py`.
- If no custom error layout is present, fall back to a simple error component.
- Avoid swallowing exceptions unless returning a user-facing error layout.

### Data/Endpoint Conventions
- Endpoint functions live in `api.py` and are named `endpoint`.
- Endpoints return serializable data (dict, list, DataFrame, etc.).
- Use helper serialization (`recursive_to_plotly_json`) when needed.

### Router/Execution Patterns
- `RouteTable` and `RouteTree` are static registries; do not instantiate.
- Use `RouteConfig` for route metadata (static routes, titles, defaults).
- Use `ChildContainer`, `SlotContainer`, and `LacyContainer` to render
  nested and lazy elements.

### General Guidance
- Keep changes localized and consistent with existing module patterns.
- Prefer clarity over cleverness; this code is used by external apps.

## Quick References
- Primary router: `flash_router/router.py`
- Core types: `flash_router/core/routing.py`
- Execution flow: `flash_router/core/execution.py`
- Helper utilities: `flash_router/utils/helper_functions.py`

## Notes for Agentic Work
- This repository currently has no automated lint/test gates.
- If you add a tool, document it here and keep defaults minimal.
- Avoid large refactors unless explicitly requested.
