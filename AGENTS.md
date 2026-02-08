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
- Automated tests use pytest; run `poetry run pytest`.
- Unit tests live in `tests/unit_tests` and can be run directly with pytest.
- Basic run: `poetry run python test.py`
- Test app: `poetry run python tests/test_app.py`
  - Dumps route table/tree JSON to `tests/utils/route_table.json` and
    `tests/utils/route_tree.json`.
- Example pages in `tests/pages` include `projects/[team_id]/files/[__rest]` for
  catch-all routing behavior.
- Example pages in `tests/pages` include `tickets/[ticket_id]/(detail)` and
  `tickets/[ticket_id]/(activity)` for nested routes with slot child nodes.

### Single Test
- Use pytest for single tests:
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
- Prefer Pydantic v2 `ConfigDict` over class-based `Config` to avoid deprecation warnings.

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
- Path template layouts are rendered with the template variable set to `None`
  when the URL omits that segment (e.g., `/projects` renders
  `projects/[team_id]` with `team_id=None`), which is the current default-layout
  behavior.

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

## Features

### Catch-All Routes (`[__rest]`)
- **Definition**: A catch-all is a path template node named `[__rest]` that
  captures all remaining URL segments and exposes them as a list `rest`.
- **Placement**: Catch-all nodes must be the last node in their branch, but they
  can still define slots.
- **Active node semantics**: The active node is the last already-rendered node
  in the branch. For deep catch-all paths, the active node remains the parent
  route (e.g., `projects/[team_id]/files`), while `[__rest]` renders as the leaf
  layout within that branch; if `/files` is the root and the URL is
  `/files/1/2/3`, the active node remains `files`.
- **Captured values**:
  - `/projects/alpha/files` -> `rest == []`
  - `/projects/alpha/files/1` -> `rest == ["1"]`
  - `/projects/alpha/files/1/2/3` -> `rest == ["1", "2", "3"]`

## Potential Improvements
- **Route priority rules**: Define explicit precedence for static vs dynamic vs
  catch-all and document conflict resolution at the same path depth.
- **Optional catch-all**: Consider a distinct optional catch-all (e.g.,
  `[[...rest]]`) vs the current `[__rest]` behavior that accepts empty lists.
- **Route groups**: Document or formalize non-routing folders (similar to Next
  route groups) beyond `ignore_empty_folders`, distinct from slots.
- **Search re-render rules**: Clarify how query param changes map to nodes,
  including Pydantic model matching and `None` for missing params.
- **Custom 404 / not found**: Provide a documented pattern for custom 404
  layouts instead of the default H1.
- **Programmatic navigation**: Add a public helper for URL generation and
  navigation (push/replace), especially for `[param]` and `[__rest]`.
- **Route guards / middleware**: Define hooks (e.g., before layout execution)
  for auth checks and redirects.
- **Metadata aggregation**: Specify how `RouteConfig` metadata composes across
  nested routes (title, description, images).
- **Prefetch / data caching**: Consider prefetching route data and caching
  endpoint results to reduce re-render work.

## Notes for Agentic Work
- This repository currently has no automated lint/test gates.
- If you add a tool, document it here and keep defaults minimal.
- Avoid large refactors unless explicitly requested.
